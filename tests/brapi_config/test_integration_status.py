import httpx
import pytest

from nexo.application.assets.market_integration import GetMarketIntegrationStatus
from nexo.application.assets.market_integration import (
    TestMarketConnection as CheckConnection,
)
from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketCredentialsRequiredError,
    MarketDataUnavailableError,
    MarketInvalidTokenError,
    MarketPlanAccessError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.cache import CachedMarketDataProvider
from nexo.infrastructure.market_data.config import PUBLIC_SYMBOLS, MarketSettings


def quote_payload(symbol="PETR4"):
    return {
        "results": [
            {
                "requestedSymbol": symbol,
                "symbol": symbol,
                "data": {"regularMarketPrice": 40, "currency": "BRL"},
            }
        ]
    }


def test_status_and_cache_capability_never_expose_token():
    def forbidden(request):
        pytest.fail("Status must not perform HTTP")

    with httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(token="TEST_TOKEN"), client=client)
        status = GetMarketIntegrationStatus(raw).execute()
        assert (
            status.configured
            and status.authenticated is None
            and status.provider == "brapi"
        )
        assert status.public_symbols == PUBLIC_SYMBOLS
        assert "TEST_TOKEN" not in repr(status) and "TEST_TOKEN" not in repr(
            raw._settings
        )
        assert CachedMarketDataProvider(raw, raw).get_integration_status() == status


@pytest.mark.parametrize("symbol", PUBLIC_SYMBOLS)
def test_all_public_symbols_work_without_token(symbol):
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json=quote_payload(symbol))
        )
    ) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        assert raw.get_quote(Asset(symbol)).price == 40
        assert not raw.get_integration_status().configured


@pytest.mark.parametrize("operation", ["quote", "history", "fundamentals", "dividends"])
def test_itsa3_without_token_requires_configuration_not_asset_not_found(operation):
    from datetime import date

    def forbidden(request):
        pytest.fail("Protected symbol must fail locally without credentials")

    with httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        with pytest.raises(MarketCredentialsRequiredError) as caught:
            if operation == "quote":
                raw.get_quote(Asset("ITSA3"))
            elif operation == "history":
                raw.get_history(Asset("ITSA3"), "1mo")
            elif operation == "fundamentals":
                raw.get_fundamentals(Asset("ITSA3"))
            else:
                raw.get_dividends(Asset("ITSA3"), date(2025, 10, 7), date(2026, 10, 6))
        assert not isinstance(caught.value, AssetNotFoundError)
        assert ".env" in str(caught.value)
        assert all(symbol in str(caught.value) for symbol in PUBLIC_SYMBOLS)


def test_protected_ticker_can_be_found_before_configuration_required():
    def handler(request):
        assert request.url.path == "/api/v2/tickers"
        return httpx.Response(
            200,
            json={
                "results": [
                    {"symbol": "ITSA3", "longName": "Itaúsa", "currency": "BRL"}
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        assert raw.search_assets("ITSA")[0].asset == Asset("ITSA3")
        with pytest.raises(MarketCredentialsRequiredError):
            raw.get_quote(Asset("ITSA3"))


def test_fake_environment_token_is_used_in_bearer_header_only(
    tmp_path, monkeypatch, clean_brapi_environment
):
    monkeypatch.setenv("BRAPI_TOKEN", "TEST_TOKEN")
    settings = MarketSettings.from_environment(tmp_path / ".env")

    def handler(request):
        auth_ok = request.headers.get("authorization") == "Bearer TEST_TOKEN"
        url_safe = (
            "TEST_TOKEN" not in str(request.url) and "token" not in request.url.params
        )
        assert auth_ok, "Bearer header incorreto"
        assert url_safe, "Credencial não pode ir na URL"
        return httpx.Response(200, json=quote_payload("ITSA3"))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert (
            BrapiMarketDataProvider(settings, client=client)
            .get_quote(Asset("ITSA3"))
            .price
            == 40
        )


@pytest.mark.parametrize(
    "http_status,error_type,state,authenticated,text",
    [
        (401, MarketInvalidTokenError, "invalid_token", False, "não foi aceita"),
        (403, MarketPlanAccessError, "plan_denied", True, "plano atual"),
        (429, MarketRateLimitError, "rate_limited", None, "limite de consultas"),
    ],
)
def test_http_failures_have_distinct_safe_diagnostics(
    http_status, error_type, state, authenticated, text
):
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                http_status, json={"error": "TEST_TOKEN secret raw"}
            )
        )
    ) as client:
        raw = BrapiMarketDataProvider(MarketSettings(token="TEST_TOKEN"), client=client)
        with pytest.raises(error_type) as caught:
            raw.get_quote(Asset("ITSA3"))
        assert "TEST_TOKEN" not in str(caught.value)
        status = CheckConnection(raw).execute()
        assert (
            status.state == state
            and status.authenticated is authenticated
            and text in status.message
        )
        assert "TEST_TOKEN" not in repr(status)


@pytest.mark.parametrize(
    "network_error", [httpx.ReadTimeout("TEST_TOKEN"), httpx.ConnectError("TEST_TOKEN")]
)
def test_network_failures_are_sanitized(network_error):
    def handler(request):
        raise network_error

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(token="TEST_TOKEN"), client=client)
        with pytest.raises(MarketDataUnavailableError) as caught:
            raw.get_quote(Asset("PETR4"))
        assert "TEST_TOKEN" not in str(caught.value)
        status = CheckConnection(raw).execute()
        assert (
            status.state == "unavailable"
            and status.authenticated is None
            and "conexão" in status.message
        )


@pytest.mark.parametrize("configured", [False, True])
def test_connection_test_makes_fresh_small_request_with_same_client(configured):
    calls = []

    def handler(request):
        calls.append(request)
        assert (
            request.url.path == "/api/v2/stocks/quote"
            and request.url.params["symbols"] == "PETR4"
        )
        auth_ok = ("authorization" in request.headers) is configured
        assert auth_ok
        return httpx.Response(200, json=quote_payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(
            MarketSettings(token="TEST_TOKEN" if configured else None), client=client
        )
        case = CheckConnection(raw)
        for _ in range(2):
            status = case.execute()
            assert status.state == "connected" and status.configured is configured
            assert (
                status.authenticated is None
            )  # A public quote cannot prove protected access.
        assert len(calls) == 2
