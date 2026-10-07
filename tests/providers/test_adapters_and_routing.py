from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from threading import Event
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from nexo.calculations.indicators.fundamentals import (
    annual_dividend,
    fundamental_indicators,
)
from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    MarketPlanAccessError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.adapters.bolsai import BolsaiProvider
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.adapters.yahoo import (
    YahooFinanceProvider,
    yahoo_symbol,
)
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.infrastructure.market_data.routing import (
    RoutedCorporateActions,
    RoutedDividendDataProvider,
    RoutedFundamentalDataProvider,
    RoutedMarketDataProvider,
)

A = Asset("ITSA4")


def bolsai(policy, payload, status=200):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["X-API-Key"] == "fixture-only"
        assert "fixture-only" not in str(request.url)
        return httpx.Response(
            status, json=payload, headers={"X-RateLimit-Remaining": "198"}
        )

    provider = BolsaiProvider(
        MarketSettings(bolsai_api_key="fixture-only"),
        policy,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return provider, calls


def brapi(policy, payload, status=200):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json=payload)

    provider = BrapiMarketDataProvider(
        MarketSettings(token="fixture-only"),
        usage=policy.usage,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return provider, calls


def yahoo(policy):
    queries = []
    frame = pd.DataFrame(
        {
            "Close": [10.0, 11.0],
            "Open": [9.0, 10.0],
            "High": [11.0, 12.0],
            "Low": [8.0, 9.0],
            "Volume": [100, 200],
            "Dividends": [0.5, 0.0],
            "Stock Splits": [0.0, 2.0],
        },
        index=pd.date_range("2026-10-01", periods=2, tz="America/Sao_Paulo"),
    )

    def factory(symbol):
        queries.append(symbol)

        def history(**kwargs):
            assert kwargs["auto_adjust"] is False and kwargs["actions"] is True
            return frame

        return SimpleNamespace(history=history)

    return YahooFinanceProvider(policy.usage, ticker_factory=factory), queries


def test_bolsai_company_exact_identity_and_long_cache(policy):
    api, calls = bolsai(
        policy,
        {
            "ticker_primary": "ITSA4",
            "queried_ticker": "ITSA4",
            "tickers": ["ITSA3", "ITSA4"],
            "corporate_name": "ITAUSA S.A.",
            "cnpj": "61.532.644/0001-15",
            "cvm_code": "7617",
            "trade_name": "ITAUSA",
            "sector": "Financeiro",
            "status": "ATIVO",
        },
    )
    first = api.get_company_identity(A)
    assert first.cnpj == "61532644000115" and first.cvm_code == "7617"
    assert api.get_company_identity(A) == first and len(calls) == 1
    assert calls[0].url.path == "/api/v1/companies/ITSA4"
    assert policy.remaining["bolsai"] == 198


@pytest.mark.parametrize(
    "payload",
    [
        {"ticker_primary": "ITSA3", "queried_ticker": "ITSA3", "tickers": ["ITSA3"]},
        {"ticker_primary": "ITSA4", "tickers": ["ITSA4"]},
    ],
)
def test_invalid_company_mapping_never_guesses_identity(policy, payload):
    api, _ = bolsai(policy, payload)
    with pytest.raises(MarketDataUnavailableError):
        api.get_company_identity(A)


def test_fundamentals_map_all_direct_fields_and_percentage_units(policy):
    fields = {
        "lpa": "1.2",
        "vpa": "10",
        "pl": "99",
        "pvp": "3",
        "ev_ebitda": "2",
        "roe": "20",
        "roa": "10",
        "roic": "15",
        "net_margin": "30",
        "gross_margin": "40",
        "ebitda_margin": "50",
        "debt_equity": "1",
        "net_debt_ebitda": "2",
        "current_ratio": "3",
        "market_cap": "1000",
        "net_revenue": "100",
        "net_income": "30",
        "equity": "200",
        "total_debt": "50",
        "cash": "10",
        "total_assets": "300",
        "ebit": "45",
        "ebitda": "50",
    }
    api, calls = bolsai(
        policy, {"queried_ticker": "ITSA4", "reference_date": "2026-06-30", **fields}
    )
    f = api.get_fundamentals(A)
    assert (
        f.eps == Decimal("1.2")
        and f.roe == Decimal("0.2")
        and f.ebitda_margin == Decimal("0.5")
    )
    assert (
        f.net_income == 30 and f.total_assets == 300 and f.debt == 50 and f.ebit == 45
    )
    indicators = {i.key: i for i in fundamental_indicators(f, None, None)}
    assert indicators["pe"].value == 99 and indicators["pe"].origin == "bolsai.pe"
    assert indicators["ebitda_margin"].value == Decimal("0.5")
    assert len(indicators) == 24 and len(calls) == 1


def test_partial_fundamentals_preserve_none_without_fake_zero(policy):
    api, _ = bolsai(policy, {"queried_ticker": "ITSA4", "lpa": "1", "roe": "bad"})
    f = api.get_fundamentals(A)
    assert f.eps == 1 and f.roe is f.revenue is f.equity is None and f.issues


def test_bolsai_eod_does_not_invent_market_timestamp_or_change(policy):
    api, calls = bolsai(
        policy,
        {
            "ticker": "ITSA4",
            "trade_date": "2026-10-06",
            "close": "11.2",
            "high": "11.5",
            "low": "11.0",
            "open": "11.1",
            "volume": 1234,
        },
    )
    q = api.get_quote(A)
    assert q.source == "bolsai" and q.price_kind == "eod" and "EOD" in q.freshness
    assert q.day_high == Decimal("11.5") and q.volume == 1234
    assert q.market_time is q.change is q.market_cap is None and q.latency_ms >= 0
    assert len(calls) == 1


def test_snapshot_full_brapi_and_default_one_ticker(policy):
    api, calls = brapi(
        policy,
        {
            "results": [
                {
                    "symbol": "ITSA4",
                    "data": {
                        "regularMarketPrice": 10,
                        "currency": "BRL",
                        "regularMarketChange": 1,
                        "regularMarketChangePercent": 2,
                        "regularMarketDayHigh": 11,
                        "regularMarketDayLow": 9,
                        "regularMarketOpen": 9.5,
                        "regularMarketPreviousClose": 9,
                        "regularMarketVolume": 123,
                        "marketCap": 1000,
                        "regularMarketTime": "2026-10-07T12:00:00Z",
                    },
                }
            ]
        },
    )
    q = api.get_quote(A)
    assert MarketSettings().batch_size == 1
    assert (
        q.price,
        q.change,
        q.change_percent,
        q.day_high,
        q.day_low,
        q.volume,
        q.market_cap,
    ) == (10, 1, 2, 11, 9, 123, 1000)
    assert (
        q.latency_ms >= 0
        and q.estimated_delay_minutes == 30
        and "30 min" in q.freshness
    )
    assert q.market_time == datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    assert len(calls) == policy.usage.count("brapi") == 1


def test_quote_fallback_cached_eod_prevents_retrying_failed_primary(policy):
    primary, primary_calls = brapi(policy, {}, status=503)
    fallback, fallback_calls = bolsai(
        policy, {"ticker": "ITSA4", "trade_date": "2026-10-06", "close": 11}
    )
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    assert router.get_quote(A).source == "bolsai"
    assert router.get_quote(A).price_kind == "eod"
    assert len(primary_calls) == len(fallback_calls) == 1


def test_petr4_brapi_priority_never_calls_bolsai_when_primary_succeeds(policy):
    asset = Asset("PETR4")
    primary, primary_calls = brapi(policy, {"results": [{
        "symbol": "PETR4", "data": {"regularMarketPrice": 30, "currency": "BRL"}
    }]})
    fallback, fallback_calls = bolsai(policy, {}, status=503)
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    assert router.get_quote(asset).source == "brapi"
    assert len(primary_calls) == 1 and not fallback_calls


def test_failed_fallback_does_not_hide_primary_local_budget(policy):
    policy.usage.budgets["brapi"] = 0
    primary, primary_calls = brapi(policy, {})
    fallback, fallback_calls = bolsai(policy, {}, status=503)
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    with pytest.raises(MarketRateLimitError) as failure:
        router.get_quote(Asset("PETR4"))
    assert "brapi (prioritária): Budget local atingido" in str(failure.value)
    assert "bolsai (fallback): bolsai: resposta HTTP 503" in str(failure.value)
    assert not primary_calls and len(fallback_calls) == 1
    assert "fixture-only" not in str(failure.value)


def test_explicit_refresh_returns_to_brapi_after_budget_fallback(policy):
    asset = Asset("PETR4")
    policy.usage.budgets["brapi"] = 0
    primary, calls = brapi(policy, {"results": [{
        "symbol": "PETR4", "data": {"regularMarketPrice": 30, "currency": "BRL"}
    }]})
    fallback, fallback_calls = bolsai(policy, {
        "ticker": "PETR4", "trade_date": "2026-10-06", "close": 29
    })
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    assert router.get_quote(asset).source == "bolsai"
    assert not calls
    router.invalidate(asset)
    with router.refresh_context(True):
        assert router.get_quote(asset).source == "brapi"
    assert len(calls) == len(fallback_calls) == 1


@pytest.mark.parametrize("status", [302, 500, 503])
def test_bolsai_unexpected_http_status_is_reported_without_response_body(policy, status):
    api, _ = bolsai(policy, {"secret": "fixture-only"}, status=status)
    with pytest.raises(MarketDataUnavailableError, match=f"HTTP {status}") as failure:
        api._request("/stocks/PETR4/quote", "quote")
    assert "fixture-only" not in str(failure.value)


def test_bolsai_timeout_is_distinct_from_invalid_json(policy):
    def handler(request):
        raise httpx.ReadTimeout("fixture-only", request=request)

    api = BolsaiProvider(MarketSettings(bolsai_api_key="fixture-only"), policy,
                        client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(MarketDataUnavailableError, match="tempo limite") as failure:
        api._request("/stocks/PETR4/quote", "quote")
    assert "fixture-only" not in str(failure.value)


@pytest.mark.parametrize(
    "period,brapi_count", [("1mo", 1), ("3mo", 1), ("1y", 0), ("5y", 0)]
)
def test_history_routing_skips_brapi_for_long_period(policy, period, brapi_count):
    primary, calls = brapi(policy, {}, status=503)
    fallback, _ = bolsai(policy, {})
    yf, queries = yahoo(policy)
    router = RoutedMarketDataProvider(primary, fallback, yf, policy)
    assert router.get_history(A, period).source == "Yahoo Finance"
    router.get_history(A, period)
    assert len(calls) == brapi_count and queries == ["ITSA4.SA"]


def test_short_history_success_keeps_priority(policy):
    primary, calls = brapi(
        policy,
        {
            "results": [
                {
                    "symbol": "ITSA4",
                    "data": {
                        "historicalDataPrice": [
                            {"date": "2026-10-01T12:00:00Z", "close": 10}
                        ]
                    },
                }
            ]
        },
    )
    fallback, _ = bolsai(policy, {})
    yf, queries = yahoo(policy)
    router = RoutedMarketDataProvider(primary, fallback, yf, policy)
    assert (
        router.get_history(A, "1mo").source == "brapi"
        and len(calls) == 1
        and not queries
    )


def test_yahoo_dividend_dates_types_source_and_bazin(policy):
    yf, queries = yahoo(policy)
    summary = yf.get_dividends(A, date(2026, 1, 1), date(2026, 10, 7))
    event = summary.events[0]
    assert event.asset == A and event.event_type == "CASH_DISTRIBUTION"
    assert event.payment_date is None and event.ex_date == date(2026, 10, 1)
    assert event.amount_per_share == Decimal("0.5") and summary.date_basis == "ex_date"
    assert (
        summary.source == "Yahoo Finance" and summary.limitations and event.limitations
    )
    assert annual_dividend(summary) == Decimal("0.5") and queries == ["ITSA4.SA"]


def test_dividends_yahoo_first_brapi_disabled_and_cache(policy):
    yf, queries = yahoo(policy)
    primary, calls = brapi(policy, {}, status=403)
    router = RoutedDividendDataProvider(yf, primary, policy)
    for _ in range(3):
        assert (
            router.get_dividends(A, date(2026, 1, 1), date(2026, 10, 7)).source
            == "Yahoo Finance"
        )
    assert len(queries) == 1 and not calls


@pytest.mark.parametrize("enabled,expected", [(False, 0), (True, 1)])
def test_dividend_brapi_capability_gate_and_negative_cache(policy, enabled, expected):
    class FailedYahoo:
        def get_dividends(self, *args):
            raise MarketDataUnavailableError("offline")

    primary, calls = brapi(policy, {}, status=403)
    router = RoutedDividendDataProvider(
        FailedYahoo(), primary, policy, brapi_enabled=enabled
    )
    for _ in range(2):
        with pytest.raises((MarketDataUnavailableError, MarketPlanAccessError)):
            router.get_dividends(A, date(2026, 1, 1), date(2026, 10, 7))
    assert len(calls) == expected


def test_budget_blocks_adapter_before_request(policy):
    api, calls = bolsai(
        policy, {"ticker": "ITSA4", "trade_date": "2026-10-06", "close": 11}
    )
    policy.usage.budgets["bolsai"] = 0
    with pytest.raises(MarketRateLimitError):
        api.get_quote(A)
    assert not calls and policy.usage.count("bolsai") == 0


def test_fundamental_priority_and_raw_official_fallback(policy):
    api, calls = bolsai(policy, {"queried_ticker": "ITSA4", "lpa": 1})

    class Official:
        def get_statements(self, asset):
            raise AssertionError("CVM must not replace valid bolsai inputs")

    router = RoutedFundamentalDataProvider(api, Official(), policy)
    assert router.get_fundamentals(A).source == "bolsai"
    router.get_fundamentals(A)
    assert len(calls) == 1


@pytest.mark.parametrize("status", [200, 503])
def test_brapi_fundamentals_take_priority_and_reuse_cache(policy, status):
    fallback, bolsai_calls = bolsai(policy, {}, status=status)
    primary, brapi_calls = brapi(
        policy,
        {"results": [{"symbol": A.symbol, "data": {"trailingEps": 4, "bookValue": 20}}]},
    )

    class Official:
        def get_statements(self, asset):
            raise AssertionError("Valid brapi inputs must precede CVM")

    router = RoutedFundamentalDataProvider(
        fallback, Official(), policy, brapi=primary
    )
    for _ in range(2):
        result = router.get_fundamentals(A)
        assert result.source == "brapi" and result.eps == 4 and result.bvps == 20
    assert not bolsai_calls and len(brapi_calls) == 2


@pytest.mark.parametrize("status", [200, 503])
def test_fundamentals_use_bolsai_only_after_brapi_failure_or_empty(policy, status):
    primary, brapi_calls = brapi(
        policy, {"results": [{"symbol": A.symbol, "data": {}}]}, status=status
    )
    fallback, bolsai_calls = bolsai(policy, {"queried_ticker": A.symbol, "lpa": 3})
    router = RoutedFundamentalDataProvider(fallback, None, policy, brapi=primary)
    for _ in range(2):
        result = router.get_fundamentals(A)
        assert result.source == "bolsai" and result.eps == 3
    assert len(brapi_calls) == 2 and len(bolsai_calls) == 1


def test_search_falls_back_to_bolsai_without_screener(policy):
    primary, _ = brapi(policy, {}, status=503)
    fallback, calls = bolsai(
        policy, {"data": [{"ticker_primary": "ITSA4", "corporate_name": "ITAUSA"}]}
    )
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    for _ in range(2):
        result = router.search_assets("itsa")
        assert result[0].source == "bolsai" and result[0].asset == A
    assert len(calls) == 1 and calls[0].url.path == "/api/v1/companies"


@pytest.mark.parametrize("symbol", ["PETR4", "ITSA4", "B3SA3"])
def test_b3_symbols_map_to_yahoo_suffix(symbol):
    assert yahoo_symbol(Asset(symbol)) == symbol + ".SA"


def test_yahoo_actions_are_cached_and_do_not_touch_ledger(policy):
    yf, queries = yahoo(policy)
    router = RoutedCorporateActions(yf, None, policy)
    actions = router.get_actions(A)
    assert actions[0].split_ratio == 2 and actions[0].source == "Yahoo Finance"
    assert router.get_actions(A) == actions and len(queries) == 1


def test_parallel_quotes_coalesce_the_entire_failed_primary_fallback_route(policy):
    started, release = Event(), Event()
    primary_calls = []

    def handler(request):
        primary_calls.append(request)
        started.set()
        assert release.wait(3)
        return httpx.Response(503)

    primary = BrapiMarketDataProvider(
        MarketSettings(token="fixture-only"),
        usage=policy.usage,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    fallback, fallback_calls = bolsai(
        policy, {"ticker": "ITSA4", "trade_date": "2026-10-06", "close": 11}
    )
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    with ThreadPoolExecutor(max_workers=3) as pool:
        first = pool.submit(router.get_quote, A)
        assert started.wait(3)
        second = pool.submit(router.get_quote, A)
        third = pool.submit(router.get_quote, A)
        release.set()
        assert first.result() == second.result() == third.result()
    assert len(primary_calls) == len(fallback_calls) == 1


def test_empty_primary_history_does_not_mask_cached_yahoo_fallback(policy):
    primary, calls = brapi(
        policy, {"results": [{"symbol": "ITSA4", "data": {"historicalDataPrice": []}}]}
    )
    yf, queries = yahoo(policy)
    router = RoutedMarketDataProvider(primary, None, yf, policy)
    for _ in range(3):
        assert router.get_history(A, "1mo").source == "Yahoo Finance"
    assert len(calls) == len(queries) == 1


def test_empty_primary_search_does_not_mask_cached_bolsai_results(policy):
    primary, primary_calls = brapi(policy, {"results": []})
    fallback, calls = bolsai(
        policy, {"data": [{"ticker_primary": "ITSA4", "corporate_name": "ITAUSA"}]}
    )
    router = RoutedMarketDataProvider(primary, fallback, None, policy)
    for _ in range(3):
        assert router.search_assets("ITSA")[0].source == "bolsai"
    assert len(calls) == len(primary_calls) == 1


def test_roe_only_is_a_valid_partial_fundamental_snapshot(policy):
    api, calls = bolsai(policy, {"queried_ticker": "ITSA4", "roe": 20})
    router = RoutedFundamentalDataProvider(api, None, policy)
    assert router.get_fundamentals(A).roe == Decimal("0.2")
    assert router.get_fundamentals(A).eps is None and len(calls) == 1


def test_yahoo_missing_optional_ohlcv_becomes_none(policy):
    frame = pd.DataFrame(
        {"Close": [10], "High": [float("nan")], "Volume": [float("nan")]},
        index=pd.date_range("2026-10-01", periods=1, tz="UTC"),
    )
    history = YahooFinanceProvider.normalize_history(A, "1y", frame)
    assert (
        history.points[0].close == 10
        and history.points[0].high is history.points[0].volume is None
    )


def test_quota_header_zero_blocks_new_remote_call_until_utc_reset(policy):
    from datetime import timedelta

    policy.update_quota("bolsai", 0)
    api, calls = bolsai(policy, {})
    with pytest.raises(MarketRateLimitError, match="Quota bolsai"):
        api.get_fundamentals(A)
    assert not calls and policy.usage.count("bolsai") == 0
    policy.usage._now = lambda: (
        datetime(2026, 10, 7, tzinfo=timezone.utc) + timedelta(days=1)
    )
    assert policy.quota_remaining("bolsai") is None


def test_yahoo_rate_limit_has_distinct_health_without_raw_exception(policy):
    from yfinance.exceptions import YFRateLimitError

    def factory(_):
        def history(**kwargs):
            raise YFRateLimitError()

        return SimpleNamespace(history=history)

    yf = YahooFinanceProvider(policy.usage, ticker_factory=factory)
    with pytest.raises(MarketRateLimitError, match="Yahoo Finance"):
        policy.call(
            "Yahoo Finance", "history", (A, "1y"), lambda: yf.get_history(A, "1y")
        )
    assert policy.health("Yahoo Finance", True, "history").status == "rate limited"


def test_percentage_normalization_preserves_provider_precision(policy):
    from decimal import localcontext

    api, _ = bolsai(
        policy, {"queried_ticker": "ITSA4", "roe": "26.1234567890123456789"}
    )
    with localcontext() as context:
        context.prec = 3
        assert api.get_fundamentals(A).roe == Decimal("0.261234567890123456789")
