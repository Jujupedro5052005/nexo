import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event

import pytest

from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    MarketPlanAccessError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.policy import (
    TTL,
    ProviderUsage,
    explicit_refresh,
)


@pytest.mark.parametrize(
    "provider,capability,seconds",
    [
        ("brapi", "quote", 60),
        ("brapi", "search", 900),
        ("brapi", "history", 1800),
        ("bolsai", "quote", 21600),
        ("bolsai", "company", 604800),
        ("bolsai", "fundamentals", 43200),
        ("Yahoo Finance", "dividends", 43200),
        ("Yahoo Finance", "history", 3600),
        ("Yahoo Finance", "actions", 43200),
        ("CVM", "registry", 86400),
        ("CVM", "statements", 86400),
    ],
)
def test_exact_ttl_cache_hit_makes_zero_remote_requests(
    policy, provider, capability, seconds
):
    clock = [0]
    policy.clock = lambda: clock[0]
    calls = []

    def remote():
        policy.usage.reserve(provider, capability)
        calls.append(1)
        return len(calls)

    assert TTL[provider, capability] == seconds
    assert policy.call(provider, capability, ("PETR4",), remote) == 1
    clock[0] = seconds - 1
    assert policy.call(provider, capability, ("PETR4",), remote) == 1
    assert policy.usage.count(provider) == 1
    clock[0] = seconds
    assert policy.call(provider, capability, ("PETR4",), remote) == 2


def test_negative_capability_is_shared_between_assets_and_expires_in_12h(policy):
    clock, calls = [0], []
    policy.clock = lambda: clock[0]

    def denied():
        policy.usage.reserve("brapi", "dividends")
        calls.append(1)
        raise MarketPlanAccessError("plan restricted")

    for symbol in ("PETR4", "ITSA4", "B3SA3"):
        with pytest.raises(MarketPlanAccessError):
            policy.call("brapi", "dividends", (symbol,), denied)
    assert len(calls) == policy.usage.count("brapi") == 1
    assert policy.health("brapi", True, "quotes").restricted_capabilities == (
        "dividends",
    )
    policy.call("brapi", "quote", ("PETR4",), lambda: 42)
    assert policy.health("brapi", True, "quotes").status == "available"
    clock[0] = 43200
    with pytest.raises(MarketPlanAccessError):
        policy.call("brapi", "dividends", ("ITSA4",), denied)
    assert len(calls) == 2


def test_soft_budget_blocks_before_transport_and_explicit_refresh_can_override(
    tmp_path,
):
    usage = ProviderUsage(tmp_path / "usage.json", {"bolsai": 1})
    usage.reserve("bolsai", "quote")
    with pytest.raises(MarketRateLimitError, match="local"):
        usage.reserve("bolsai", "fundamentals")
    assert usage.count("bolsai") == 1
    with explicit_refresh():
        usage.reserve("bolsai", "fundamentals")
    assert usage.count("bolsai") == 2
    with pytest.raises(MarketRateLimitError):
        usage.reserve("bolsai", "quote")


def test_counter_persists_without_secrets_and_resets_at_midnight_utc(tmp_path):
    now = [datetime(2026, 10, 7, 23, 59, tzinfo=timezone.utc)]
    path = tmp_path / "usage.json"
    budgets = {"brapi": 100}
    first = ProviderUsage(path, budgets, now=lambda: now[0])
    first.reserve("brapi", "quote")
    second = ProviderUsage(path, budgets, now=lambda: now[0])
    second.reserve("brapi", "search")
    assert first.count("brapi") == 2
    data = json.loads(path.read_text())
    assert data == {"date": "2026-10-07", "usage": {"brapi": {"quote": 1, "search": 1}}}
    now[0] += timedelta(minutes=1)
    assert second.count("brapi") == 0


def test_counter_failure_is_fail_closed(tmp_path):
    path = tmp_path / "usage.json"
    path.write_text("not json")
    usage = ProviderUsage(path, {"brapi": 100})
    with pytest.raises(MarketDataUnavailableError):
        usage.reserve("brapi", "quote")
    assert path.read_text() == "not json"


@pytest.mark.parametrize(
    "capability", ["quote", "search", "history", "fundamentals", "company"]
)
def test_concurrent_identical_requests_coalesce(policy, capability):
    provider = "bolsai" if capability in {"fundamentals", "company"} else "brapi"
    entered, release = Event(), Event()
    calls = []

    def remote():
        calls.append(1)
        entered.set()
        assert release.wait(3)
        return 42

    with ThreadPoolExecutor(max_workers=3) as pool:
        first = pool.submit(
            policy.call, provider, capability, (Asset("PETR4"),), remote
        )
        assert entered.wait(3)
        second = pool.submit(
            policy.call, provider, capability, (Asset("PETR4"),), remote
        )
        third = pool.submit(
            policy.call, provider, capability, (Asset("PETR4"),), remote
        )
        release.set()
        assert first.result() == second.result() == third.result() == 42
    assert len(calls) == 1


def test_invalidation_during_flight_prevents_stale_repopulation(policy):
    entered, release = Event(), Event()
    asset = Asset("PETR4")

    def remote():
        entered.set()
        assert release.wait(3)
        return 1

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(policy.call, "brapi", "quote", (asset,), remote)
        assert entered.wait(3)
        policy.invalidate(asset)
        release.set()
        assert pending.result() == 1
    assert policy.call("brapi", "quote", (asset,), lambda: 2) == 2


def test_health_rate_limit_and_not_configured(policy):
    assert policy.health("bolsai", False, "fundamentals").status == "not configured"

    def limited():
        raise MarketRateLimitError("limited")

    with pytest.raises(MarketRateLimitError):
        policy.call("bolsai", "fundamentals", ("ITSA4",), limited)
    assert policy.health("bolsai", True, "fundamentals").status == "rate limited"


def test_health_offline_capability_does_not_disable_available_quote(policy):
    from nexo.domain.interfaces.market_data_provider import MarketOfflineError

    def offline():
        raise MarketOfflineError("offline")

    with pytest.raises(MarketOfflineError):
        policy.call("brapi", "history", ("ITSA4",), offline)
    assert policy.health("brapi", True, "market").status == "offline"
    policy.call("brapi", "quote", ("ITSA4",), lambda: 10)
    assert policy.health("brapi", True, "market").status == "available"
