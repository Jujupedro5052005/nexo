from datetime import datetime, timezone
from decimal import Decimal
from threading import Barrier, Lock
from types import SimpleNamespace

import pytest

from nexo.core.cancellation import OperationCancelled, current_cancellation
from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.infrastructure.market_data import yahoo_transport as transport
from nexo.infrastructure.market_data.adapters import yahoo as adapter
from nexo.infrastructure.market_data.routing import RoutedMarketDataProvider

A, B, C = Asset("PETR4"), Asset("VALE3"), Asset("B3SA3")
STAMP = datetime(2026, 10, 21, 13, tzinfo=timezone.utc)


def quote(asset):
    return Quote(
        asset,
        Decimal(30),
        "BRL",
        asset.symbol,
        STAMP,
        market_time=STAMP,
        source="Yahoo Finance",
    )


def test_public_quote_batch_does_not_fetch_company_snapshots(policy, monkeypatch):
    calls = []

    def request(symbol, method, **kwargs):
        calls.append((symbol, method, kwargs))
        return {
            "PETR4.SA": {
                "regularMarketPrice": 30,
                "currency": "BRL",
                "regularMarketTime": int(STAMP.timestamp()),
            },
            "VALE3.SA": None,
        }

    monkeypatch.setattr(adapter, "yahoo_request", request)
    provider = adapter.YahooFinanceProvider(policy.usage)
    monkeypatch.setattr(
        provider,
        "_info",
        lambda _: pytest.fail("Company fundamentals requested for batch prices"),
    )
    result = provider.get_quotes((A, B, A))
    assert calls == [("", "quotes", {"symbols": ("PETR4.SA", "VALE3.SA")})]
    assert len(result.quotes) == len(result.issues) == 1
    assert result.quotes[0].market_time == STAMP
    assert policy.usage.count("Yahoo Finance") == 1


def test_chart_metadata_preserves_time_currency_without_inventing_daily_change(
    monkeypatch,
):
    import yfinance

    calls = []
    ticker = SimpleNamespace(
        history=lambda **kw: calls.append(kw),
        get_history_metadata=lambda: {
            "regularMarketPrice": 30,
            "currency": "BRL",
            "regularMarketTime": 123,
            "chartPreviousClose": 99,
        },
    )
    monkeypatch.setattr(yfinance, "Ticker", lambda _: ticker)
    _, data = transport._quote_metadata("PETR4.SA")
    assert calls[0]["timeout"] == 6 and calls[0]["period"] == "5d"
    assert data["regularMarketTime"] == 123 and data["currency"] == "BRL"
    assert (
        "regularMarketPreviousClose" not in data and "regularMarketChange" not in data
    )


def test_child_batches_use_four_workers_and_stream_completed_symbols(monkeypatch):
    barrier = Barrier(4)
    lock = Lock()
    counts = [0, 0]
    messages = []

    def fetch(symbol):
        with lock:
            counts[0] += 1
            counts[1] = max(counts)
        barrier.wait(timeout=3)
        with lock:
            counts[0] -= 1
        return symbol, {"regularMarketPrice": 1}

    monkeypatch.setattr(transport, "_quote_metadata", fetch)
    result = transport._quote_batch(
        tuple(str(i) for i in range(8)), SimpleNamespace(send=messages.append)
    )
    assert counts[1] == 4 and len(result) == len(messages) == 8
    assert all(m[0] is None for m in messages)


def test_routing_batches_primary_and_only_complements_missing_assets(policy):
    primary_calls, fallback_calls = [], []

    def primary(assets):
        primary_calls.append(tuple(assets))
        return QuoteBatch(
            (quote(A),), (QuoteIssue(B, MarketDataUnavailableError("missing")),)
        )

    def fallback(asset):
        fallback_calls.append(asset)
        # Zero automatic budget must still accept this explicit user refresh.
        policy.usage.reserve("brapi", "quote")
        return quote(asset)

    policy.usage.budgets["brapi"] = 0
    yahoo = SimpleNamespace(
        get_quotes=primary, get_quote=lambda _: pytest.fail("Serial Yahoo retry")
    )
    market = RoutedMarketDataProvider(
        SimpleNamespace(get_quote=fallback), SimpleNamespace(), yahoo, policy
    )
    with market.refresh_context(True):
        first = market.get_quotes((A, B, A))
        second = market.get_quotes((A, B))
    assert primary_calls == [(A, B)]
    assert fallback_calls == [B]
    assert first == second and [q.asset for q in first.quotes] == [A, B]
    assert market.get_quote(A).retrieved_at == STAMP


def test_all_primary_successes_never_call_complements(policy):
    calls = []

    def primary(assets):
        calls.append(tuple(assets))
        return QuoteBatch(tuple(quote(a) for a in assets))

    def forbidden(_):
        pytest.fail("Complement queried despite available Yahoo quote")

    yahoo = SimpleNamespace(get_quotes=primary, get_quote=forbidden)
    market = RoutedMarketDataProvider(
        SimpleNamespace(get_quote=forbidden),
        SimpleNamespace(get_quote=forbidden),
        yahoo,
        policy,
    )
    assert len(market.get_quotes((A, B, C)).quotes) == 3
    assert market.get_quotes((A, B)).quotes == (quote(A), quote(B))
    assert calls == [(A, B, C)]


def test_invalidated_batch_cannot_repopulate_quote_cache(policy):
    def operation():
        policy.invalidate()
        return QuoteBatch((quote(A),))

    policy.call("Yahoo Finance", "quote_batch", (A,), operation)
    assert policy.cached("Yahoo Finance", "quote", (A,)) is None


def test_deadline_keeps_completed_prices_and_terminates_owned_child(monkeypatch):
    actions = []
    readings = iter([0, 0, 17])

    class Connection:
        def close(self):
            pass

        def poll(self, timeout):
            return True

        def recv(self):
            return None, ("PETR4.SA", {"regularMarketPrice": 30})

    class Process:
        pid = 123

        def start(self):
            pass

        def is_alive(self):
            return True

        def terminate(self):
            actions.append("terminate")

        def join(self, timeout):
            pass

        def close(self):
            pass

    context = SimpleNamespace(
        Pipe=lambda **_: (Connection(), Connection()), Process=lambda **_: Process()
    )
    monkeypatch.setattr(transport, "get_context", lambda _: context)
    monkeypatch.setattr(transport, "monotonic", lambda: next(readings))
    result = transport.yahoo_request("", "quotes", symbols=("PETR4.SA", "VALE3.SA"))
    assert result == {"PETR4.SA": {"regularMarketPrice": 30}}
    assert actions == ["terminate"]


def test_cancelled_refresh_does_not_activate_complements(policy):
    from threading import Event

    token = Event()
    calls = []

    def primary(assets):
        token.set()
        raise OperationCancelled("cancelled")

    market = RoutedMarketDataProvider(
        SimpleNamespace(get_quote=lambda a: calls.append(a)),
        SimpleNamespace(),
        SimpleNamespace(get_quotes=primary),
        policy,
    )
    context = current_cancellation.set(token)
    try:
        with pytest.raises(OperationCancelled):
            market.get_quotes((A, B))
    finally:
        current_cancellation.reset(context)
    assert not calls


def test_recovered_batch_clears_previous_individual_failure(policy):
    policy.call(
        "Yahoo Finance",
        "quote_batch",
        (A, B),
        lambda: QuoteBatch((), (QuoteIssue(B, MarketDataUnavailableError("missing")),)),
    )
    assert policy.recent_failure("Yahoo Finance", "quote", (B,))
    policy.call("Yahoo Finance", "quote_batch", (B,), lambda: QuoteBatch((quote(B),)))
    assert not policy.recent_failure("Yahoo Finance", "quote", (B,))
    assert policy.call(
        "Yahoo Finance", "quote", (B,), lambda: pytest.fail("Fresh quote ignored")
    ) == quote(B)
