from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.cache import CachedMarketDataProvider

A, B = Asset("PETR4"), Asset("VALE3")


def test_shared_quotes_deduplication_ttl_and_per_asset_invalidation(analytics_provider):
    now = [0.0]
    cache = CachedMarketDataProvider(
        analytics_provider, analytics_provider, clock=lambda: now[0]
    )
    assert len(cache.get_quotes([A, A, B]).quotes) == 2
    cache.get_quote(A)
    assert analytics_provider.calls == [(A, B)]
    now[0] = 30
    cache.get_quote(A)
    assert analytics_provider.calls == [(A, B), (A,)]
    cache.get_quote(B)
    cache.invalidate(A)
    cache.get_quotes([A, B])
    assert analytics_provider.calls[-1] == (A,)
    cache.invalidate()
    cache.get_quotes([A, B])
    assert analytics_provider.calls[-1] == (A, B)


def test_history_fundamentals_and_dividends_have_independent_keys_and_ttl(
    analytics_provider,
):
    now = [0.0]
    cache = CachedMarketDataProvider(
        analytics_provider, analytics_provider, clock=lambda: now[0]
    )
    for _ in range(2):
        cache.get_history(A, "1mo")
        cache.get_fundamentals(A)
        cache.get_dividends(A, date(2025, 10, 7), date(2026, 10, 6))
    cache.get_history(A, "1y")
    cache.get_dividends(A, date(2025, 10, 8), date(2026, 10, 7))
    assert len(analytics_provider.history_calls) == 2
    assert (
        len(analytics_provider.fund_calls) == 1
        and len(analytics_provider.div_calls) == 2
    )
    now[0] = 300
    cache.get_fundamentals(A)
    assert len(analytics_provider.fund_calls) == 2


def test_errors_and_missing_quotes_are_not_cached(analytics_provider):
    cache = CachedMarketDataProvider(analytics_provider, analytics_provider)
    analytics_provider.fund_error = MarketDataUnavailableError("offline")
    for _ in range(2):
        with pytest.raises(MarketDataUnavailableError):
            cache.get_fundamentals(A)
    assert len(analytics_provider.fund_calls) == 2
    missing = Asset("ABEV3")
    assert cache.get_quotes([A, missing]).issues
    assert cache.get_quotes([A, missing]).issues
    assert analytics_provider.calls == [(A, missing), (missing,)]


@pytest.mark.parametrize("kind", ["fundamentals", "quote"])
def test_simultaneous_requests_coalesce_without_holding_network_lock(
    analytics_provider, kind
):
    cache = CachedMarketDataProvider(analytics_provider, analytics_provider)
    operation = cache.get_fundamentals if kind == "fundamentals" else cache.get_quote
    setattr(
        analytics_provider,
        "block_fund_next" if kind == "fundamentals" else "block_quotes_next",
        True,
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(operation, A)
        try:
            assert analytics_provider.entered.wait(3)
            second = pool.submit(operation, A)
        finally:
            analytics_provider.release.set()
        assert first.result(timeout=3) == second.result(timeout=3)
    assert (
        len(
            analytics_provider.fund_calls
            if kind == "fundamentals"
            else analytics_provider.calls
        )
        == 1
    )


@pytest.mark.parametrize("kind", ["fundamentals", "quote"])
def test_invalidation_prevents_inflight_fetch_from_repopulating_cache(
    analytics_provider, kind
):
    cache = CachedMarketDataProvider(analytics_provider, analytics_provider)
    operation = cache.get_fundamentals if kind == "fundamentals" else cache.get_quote
    setattr(
        analytics_provider,
        "block_fund_next" if kind == "fundamentals" else "block_quotes_next",
        True,
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(operation, A)
        try:
            assert analytics_provider.entered.wait(3)
            cache.invalidate(A)
        finally:
            analytics_provider.release.set()
        future.result(timeout=3)
    operation(A)
    operation(A)
    assert (
        len(
            analytics_provider.fund_calls
            if kind == "fundamentals"
            else analytics_provider.calls
        )
        == 2
    )


def test_bounded_cache_eviction(analytics_provider):
    cache = CachedMarketDataProvider(
        analytics_provider, analytics_provider, max_entries=1
    )
    cache.get_quote(A)
    cache.get_quote(B)
    cache.get_quote(A)
    assert analytics_provider.calls == [(A,), (B,), (A,)]
