from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals
from nexo.infrastructure.market_data.adapters.yahoo import YahooFinanceProvider
from nexo.infrastructure.market_data.routing import (
    RoutedFundamentalDataProvider,
    RoutedMarketDataProvider,
)

A = Asset("ITSA4")


class Forbidden:
    def __getattr__(self, name):
        def fail(*args):
            raise AssertionError(f"Complement queried unnecessarily: {name}")

        return fail


def snapshot():
    return dict(  # noqa: C408 -- readable Yahoo field fixture
        regularMarketPrice=20,
        currency="BRL",
        financialCurrency="BRL",
        trailingEps=2,
        bookValue=10,
        regularMarketTime=1792587600,
        totalRevenue=1000,
        ebitda=200,
        totalDebt=100,
        totalCash=20,
        returnOnEquity=0.20,
        mostRecentQuarter=1782777600,
    )


def test_yahoo_quote_and_fundamentals_share_snapshot_without_paid_calls(policy):
    calls = []

    def info():
        calls.append(True)
        return snapshot()

    yahoo = YahooFinanceProvider(
        policy.usage, ticker_factory=lambda symbol: SimpleNamespace(get_info=info)
    )
    market = RoutedMarketDataProvider(Forbidden(), Forbidden(), yahoo, policy)
    fundamentals = RoutedFundamentalDataProvider(
        Forbidden(), Forbidden(), policy, brapi=Forbidden(), yahoo=yahoo
    )
    quote = market.get_quote(A)
    result = fundamentals.get_fundamentals(A)
    assert quote.source == result.source == "Yahoo Finance"
    assert quote.price == 20 and result.eps == 2 and result.bvps == 10
    assert quote.market_time.utcoffset().total_seconds() == 0
    assert len(calls) == policy.usage.count("Yahoo Finance") == 1
    assert policy.usage.count("brapi") == policy.usage.count("bolsai") == 0


def test_yahoo_search_returns_only_verified_brazilian_results(policy):
    yahoo = YahooFinanceProvider(
        policy.usage,
        search_factory=lambda query: [
            {"symbol": "ITSA4.SA", "longname": "Itaúsa", "quoteType": "EQUITY"},
            {"symbol": "AAPL", "longname": "Apple"},
        ],
    )
    rows = yahoo.search_assets("ITSA")
    assert len(rows) == 1 and rows[0].asset == A and rows[0].source == "Yahoo Finance"


@pytest.mark.parametrize(
    "field,value",
    [
        ("regularMarketPrice", 0),
        ("regularMarketPrice", float("nan")),
        ("currency", None),
    ],
)
def test_invalid_yahoo_quotes_are_not_made_up(policy, field, value):
    info = {**snapshot(), field: value}
    yahoo = YahooFinanceProvider(
        policy.usage,
        ticker_factory=lambda symbol: SimpleNamespace(get_info=lambda: info),
    )
    with pytest.raises(MarketDataUnavailableError):
        yahoo.get_quote(A)


def test_foreign_accounting_currency_not_used_as_brl(policy):
    info = {**snapshot(), "financialCurrency": "USD"}
    yahoo = YahooFinanceProvider(
        policy.usage,
        ticker_factory=lambda symbol: SimpleNamespace(get_info=lambda: info),
    )
    with pytest.raises(MarketDataUnavailableError, match="BRL"):
        yahoo.get_fundamentals(A)


def test_partial_yahoo_complements_only_missing_aligned_fields(policy):
    now = datetime(2026, 10, 21, tzinfo=timezone.utc)
    yahoo = SimpleNamespace(
        get_fundamentals=lambda a: CompanyFundamentals(
            a,
            now,
            eps=Decimal(2),
            reference_date=date(2026, 6, 30),
            source="Yahoo Finance",
        )
    )
    brapi = SimpleNamespace(
        get_fundamentals=lambda a: CompanyFundamentals(
            a,
            now,
            eps=Decimal(99),
            bvps=Decimal(10),
            reference_date=date(2026, 6, 30),
            source="brapi",
        )
    )
    router = RoutedFundamentalDataProvider(
        Forbidden(), Forbidden(), policy, brapi=brapi, yahoo=yahoo
    )
    result = router.get_fundamentals(A)
    assert result.eps == 2 and result.bvps == 10 and result.source == "Yahoo Finance"
    assert ("bvps", "brapi") in result.field_sources


def test_mismatched_quarters_are_never_silently_merged(policy):
    now = datetime(2026, 10, 21, tzinfo=timezone.utc)
    yahoo = SimpleNamespace(
        get_fundamentals=lambda a: CompanyFundamentals(
            a,
            now,
            eps=Decimal(2),
            reference_date=date(2026, 6, 30),
            source="Yahoo Finance",
        )
    )
    other = SimpleNamespace(
        get_fundamentals=lambda a: CompanyFundamentals(
            a, now, bvps=Decimal(10), reference_date=date(2026, 3, 31), source="brapi"
        )
    )
    router = RoutedFundamentalDataProvider(
        other, Forbidden(), policy, brapi=other, yahoo=yahoo
    )
    result = router.get_fundamentals(A)
    assert result.bvps is None and not result.field_sources


def test_failed_yahoo_cooldown_and_manual_invalidation(policy):
    calls = []

    def fail():
        calls.append(True)
        raise MarketDataUnavailableError("Offline")

    for _ in range(2):
        with pytest.raises(MarketDataUnavailableError):
            policy.call("Yahoo Finance", "quote", (A,), fail)
    assert len(calls) == 1
    policy.invalidate(A)
    with pytest.raises(MarketDataUnavailableError):
        policy.call("Yahoo Finance", "quote", (A,), fail)
    assert len(calls) == 2


def test_bad_optional_yahoo_fields_keep_valid_quote_and_avoid_paid_fallback(policy):
    info = {
        **snapshot(),
        "regularMarketVolume": float("nan"),
        "regularMarketTime": "bad",
        "regularMarketDayHigh": "bad",
    }
    yahoo = YahooFinanceProvider(
        policy.usage,
        ticker_factory=lambda symbol: SimpleNamespace(get_info=lambda: info),
    )
    market = RoutedMarketDataProvider(Forbidden(), Forbidden(), yahoo, policy)
    quote = market.get_quote(A)
    assert (
        quote.price == 20
        and quote.market_time is None
        and quote.volume is None
        and quote.day_high is None
    )


def test_yahoo_refresh_does_not_wait_for_network_or_cache_obsolete_snapshot(policy):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    entered, release = Event(), Event()
    calls = []

    def info():
        calls.append(True)
        if len(calls) == 1:
            entered.set()
            assert release.wait(3)
            return snapshot()
        return {**snapshot(), "regularMarketPrice": 21}

    yahoo = YahooFinanceProvider(
        policy.usage, ticker_factory=lambda symbol: SimpleNamespace(get_info=info)
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(yahoo.get_quote, A)
        assert entered.wait(3)
        invalidated = pool.submit(yahoo.invalidate, A)
        try:
            invalidated.result(timeout=1)
        finally:
            release.set()
        assert pending.result().price == 20
    assert yahoo.get_quote(A).price == 21 and len(calls) == 2


def test_successful_manual_retry_replaces_failure_cooldown(policy):
    def fail():
        raise MarketDataUnavailableError("Offline")

    with pytest.raises(MarketDataUnavailableError):
        policy.call("Yahoo Finance", "quote", (A,), fail)
    from nexo.infrastructure.market_data.policy import explicit_refresh

    with explicit_refresh():
        assert policy.call("Yahoo Finance", "quote", (A,), lambda: 42) == 42
    assert policy.call("Yahoo Finance", "quote", (A,), lambda: 99) == 42


def test_yahoo_connection_test_can_bypass_local_budget_without_resetting_it(policy):
    from nexo.application.assets.market_integration import TestMarketConnection
    from nexo.domain.interfaces.market_data_provider import MarketRateLimitError

    policy.usage.budgets["Yahoo Finance"] = 0
    yahoo = YahooFinanceProvider(
        policy.usage, ticker_factory=lambda symbol: SimpleNamespace(get_info=snapshot)
    )
    with pytest.raises(MarketRateLimitError):
        yahoo.get_quote(A)
    result = TestMarketConnection(yahoo).execute()
    assert result.state == "connected" and result.provider == "Yahoo Finance"
    assert policy.usage.budgets["Yahoo Finance"] == 0
    assert policy.usage.count("Yahoo Finance") == 1
