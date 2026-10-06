import json
from decimal import Decimal

import httpx
import pytest

from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketAuthenticationError,
    MarketDataUnavailableError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.config import MarketSettings


def quote_row(symbol="PETR4", **overrides):
    data = {
        "regularMarketPrice": "40.12345678901234567890123456789",
        "currency": "BRL",
        "longName": "Petrobras",
        "regularMarketTime": "2026-10-06T12:00:00Z",
        "regularMarketChange": "1.2",
        "regularMarketChangePercent": "3.4",
    }
    data.update(overrides)
    return {"requestedSymbol": symbol, "symbol": symbol, "changed": False, "data": data}


def adapter(payload, *, status=200, settings=None):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return BrapiMarketDataProvider(settings, client=client), requests


def test_v2_quotes_preserve_decimal_and_public_access():
    api, requests = adapter({"results": [quote_row()]})
    quote = api.get_quote(Asset("petr4"))
    assert quote.price == Decimal("40.12345678901234567890123456789")
    assert (
        quote.currency == "BRL" and quote.market_time.utcoffset().total_seconds() == 0
    )
    assert isinstance(quote.change, Decimal) and quote.source == "brapi"
    assert requests[0].url.path == "/api/v2/stocks/quote"
    assert "authorization" not in requests[0].headers


def test_json_numeric_literal_is_parsed_without_float_roundtrip():
    raw = json.dumps({"results": [quote_row()]}).replace(
        '"40.12345678901234567890123456789"', "40.12345678901234567890123456789"
    )
    api = BrapiMarketDataProvider(
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=raw))
        )
    )
    assert api.get_quote(Asset("PETR4")).price == Decimal(
        "40.12345678901234567890123456789"
    )


def test_batch_deduplicates_and_keeps_three_symbols_in_one_request():
    api, requests = adapter(
        {"results": [quote_row(s) for s in ("PETR4", "VALE3", "ITUB4")]}
    )
    result = api.get_quotes([Asset(s) for s in ("PETR4", "VALE3", "ITUB4", "PETR4")])
    assert len(result.quotes) == 3 and not result.issues
    assert len(requests) == 1
    assert requests[0].url.params["symbols"] == "PETR4,VALE3,ITUB4"


def test_plan_batch_limit_is_applied():
    api, requests = adapter(
        {"results": [quote_row(s) for s in ("PETR4", "VALE3", "ITUB4")]},
        settings=MarketSettings(batch_size=2),
    )
    assert (
        len(api.get_quotes([Asset(s) for s in ("PETR4", "VALE3", "ITUB4")]).quotes) == 3
    )
    assert [r.url.params["symbols"] for r in requests] == ["PETR4,VALE3", "ITUB4"]


def test_no_token_filters_restricted_symbol_without_poisoning_public_batch():
    api, requests = adapter({"results": [quote_row()]})
    result = api.get_quotes([Asset("PETR4"), Asset("ABCD3")])
    assert len(result.quotes) == 1
    assert isinstance(result.issues[0].error, MarketAuthenticationError)
    assert requests[0].url.params["symbols"] == "PETR4"
    with pytest.raises(MarketAuthenticationError):
        api.get_quote(Asset("ABCD3"))
    assert len(requests) == 1


def test_bearer_token_is_in_header_only_and_repr_is_safe():
    secret = "test-secret-not-real"
    settings = MarketSettings(token=secret)
    api, requests = adapter({"results": [quote_row("ABCD3")]}, settings=settings)
    api.get_quote(Asset("ABCD3"))
    assert requests[0].headers["authorization"] == f"Bearer {secret}"
    assert secret not in str(requests[0].url)
    assert secret not in repr(settings)


@pytest.mark.parametrize(
    "status,error",
    [
        (401, MarketAuthenticationError),
        (403, MarketAuthenticationError),
        (404, AssetNotFoundError),
        (429, MarketRateLimitError),
        (500, MarketDataUnavailableError),
        (400, MarketDataUnavailableError),
    ],
)
def test_http_errors_are_safe_boundary_errors(status, error):
    api, _ = adapter({"secret": "never-display-this-response"}, status=status)
    with pytest.raises(error) as caught:
        api.get_quote(Asset("PETR4"))
    assert "never-display" not in str(caught.value)


@pytest.mark.parametrize(
    "error",
    [httpx.ReadTimeout("secret timeout"), httpx.ConnectError("secret connection")],
)
def test_network_errors_are_translated(error):
    def fail(_):
        raise error

    api = BrapiMarketDataProvider(
        client=httpx.Client(transport=httpx.MockTransport(fail))
    )
    with pytest.raises(MarketDataUnavailableError) as caught:
        api.get_quote(Asset("PETR4"))
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    "raw", ["not JSON", '{"results": NaN}', '{"results": {}}', "{}", "[]"]
)
def test_invalid_payload_is_not_a_price(raw):
    api = BrapiMarketDataProvider(
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=raw))
        )
    )
    with pytest.raises(MarketDataUnavailableError):
        api.get_quote(Asset("PETR4"))


@pytest.mark.parametrize(
    "price", [None, "NaN", "Infinity", "-1", "0", True, {}, "garbage"]
)
def test_invalid_quote_preserves_other_symbols(price):
    api, _ = adapter(
        {"results": [quote_row(regularMarketPrice=price), quote_row("VALE3")]}
    )
    result = api.get_quotes([Asset("PETR4"), Asset("VALE3")])
    assert [q.asset.symbol for q in result.quotes] == ["VALE3"]
    assert result.issues[0].asset == Asset("PETR4")


def test_missing_quote_has_asset_not_found_issue():
    api, _ = adapter({"results": [quote_row()]})
    result = api.get_quotes([Asset("PETR4"), Asset("ITUB4")])
    assert len(result.quotes) == 1 and isinstance(
        result.issues[0].error, AssetNotFoundError
    )


def test_renamed_ticker_is_not_silently_valued_with_original_quantity():
    row = quote_row("AXIA5")
    row.update(symbol="AXIA3", changed=True)
    api, _ = adapter({"results": [row]}, settings=MarketSettings(token="fake"))
    with pytest.raises(MarketDataUnavailableError, match="Ticker alterado"):
        api.get_quote(Asset("AXIA5"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"currency": None},
        {"currency": ""},
        {"regularMarketTime": "2026-10-06T12:00:00"},
    ],
)
def test_invalid_metadata_is_unavailable(overrides):
    api, _ = adapter({"results": [quote_row(**overrides)]})
    with pytest.raises(MarketDataUnavailableError):
        api.get_quote(Asset("PETR4"))


def test_search_uses_real_catalog_endpoint_and_maps_value_objects():
    api, requests = adapter(
        {
            "results": [
                {
                    "symbol": "PETR4",
                    "name": "Petrobras",
                    "currency": "BRL",
                    "assetType": "stock",
                }
            ]
        }
    )
    result = api.search_assets(" PETR ")
    assert result[0].asset == Asset("PETR4") and result[0].name == "Petrobras"
    assert (
        requests[0].url.path == "/api/v2/tickers"
        and requests[0].url.params["search"] == "PETR"
    )


def test_history_is_decimal_chronological_and_daily():
    api, requests = adapter(
        {
            "results": [
                {
                    "symbol": "PETR4",
                    "data": {
                        "historicalDataPrice": [
                            {
                                "date": 172800,
                                "close": "31.1234567890123456789",
                                "open": "30",
                                "high": "32",
                                "low": "29",
                                "volume": 100,
                            },
                            {"date": 86400, "close": "30"},
                        ]
                    },
                }
            ]
        }
    )
    result = api.get_history(Asset("PETR4"), "3mo")
    assert (
        len(result.points) == 2
        and result.points[0].timestamp < result.points[1].timestamp
    )
    assert result.points[1].close == Decimal("31.1234567890123456789")
    assert result.points[1].volume == 100 and isinstance(result.points[1].high, Decimal)
    assert requests[0].url.path == "/api/v2/stocks/historical"
    assert dict(requests[0].url.params) == {
        "symbols": "PETR4",
        "range": "3mo",
        "interval": "1d",
        "sortOrder": "asc",
    }


def test_empty_history_is_honest_empty_state():
    api, _ = adapter(
        {"results": [{"symbol": "PETR4", "data": {"historicalDataPrice": []}}]}
    )
    assert api.get_history(Asset("PETR4"), "1mo").points == ()


def test_history_missing_asset_and_unsupported_period():
    api, requests = adapter({"results": []})
    with pytest.raises(AssetNotFoundError):
        api.get_history(Asset("PETR4"), "1mo")
    with pytest.raises(MarketDataUnavailableError):
        api.get_history(Asset("PETR4"), "5y")
    assert len(requests) == 1


def test_empty_quote_batch_makes_no_http_request():
    api, requests = adapter({"results": []})
    assert api.get_quotes([]).quotes == () and not requests


@pytest.mark.parametrize(
    "payload",
    [
        {"results": [{"symbol": "PETR4", "data": {}}]},
        {
            "results": [
                {
                    "symbol": "PETR4",
                    "data": {"historicalDataPrice": [{"date": "bad", "close": "30"}]},
                }
            ]
        },
        {
            "results": [
                {
                    "requestedSymbol": "PETR4",
                    "symbol": "VALE3",
                    "changed": True,
                    "data": {"historicalDataPrice": []},
                }
            ]
        },
    ],
)
def test_invalid_or_renamed_history_is_safe(payload):
    api, _ = adapter(payload)
    with pytest.raises(MarketDataUnavailableError):
        api.get_history(Asset("PETR4"), "1mo")


def test_bad_catalog_metadata_is_translated():
    api, _ = adapter(
        {"results": [{"symbol": "PETR4", "name": "Petrobras", "currency": 42}]}
    )
    with pytest.raises(MarketDataUnavailableError):
        api.search_assets("PETR")
