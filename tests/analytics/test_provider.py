from datetime import date
from decimal import Decimal

import httpx
import pytest

from nexo.calculations.indicators.fundamentals import annual_dividend
from nexo.domain.interfaces.market_data_provider import (
    MarketAuthenticationError,
    MarketDataError,
    MarketDataUnavailableError,
)
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.config import MarketSettings

ASSET = Asset("PETR4")
START, END = date(2025, 10, 7), date(2026, 10, 6)


def envelope(data, **extra):
    return {
        "results": [
            {"requestedSymbol": "PETR4", "symbol": "PETR4", "data": data, **extra}
        ]
    }


def provider_for(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return BrapiMarketDataProvider(MarketSettings(), client=client), client


def test_real_contract_decimal_nullable_fields_and_single_injected_client():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.params["symbols"] == "PETR4"
        assert request.url.params["mode"] == "current"
        data = (
            {
                "trailingEps": 4.25,
                "bookValue": "20.50",
                "mostRecentQuarter": "2026-06-30T00:00:00.000Z",
            }
            if request.url.path.endswith("statistics")
            else {
                "returnOnEquity": 0.277,
                "returnOnAssets": None,
                "profitMargins": 0.2,
                "totalRevenue": 1000,
                "ebitda": 300,
                "totalDebt": 200,
                "totalCash": 100,
                "financialCurrency": None,
            }
        )
        return httpx.Response(200, json=envelope(data))

    provider, client = provider_for(handler)
    try:
        result = provider.get_fundamentals(ASSET)
        assert result.eps == Decimal("4.25") and result.bvps == Decimal("20.50")
        assert result.roe == Decimal("0.277") and result.roa is None
        assert result.reference_date == date(2026, 6, 30) and result.currency == "BRL"
        assert len(requests) == 2 and not result.issues
    finally:
        client.close()


@pytest.mark.parametrize("invalid", [True, "NaN", "Infinity", "oops", []])
def test_invalid_one_field_preserves_remaining_fundamentals(invalid):
    def handler(request):
        data = (
            {"trailingEps": invalid, "earningsPerShare": "3", "bookValue": "20"}
            if request.url.path.endswith("statistics")
            else {}
        )
        return httpx.Response(200, json=envelope(data))

    provider, client = provider_for(handler)
    try:
        result = provider.get_fundamentals(ASSET)
        assert result.eps == 3 and result.bvps == 20 and result.revenue is None
        assert any("trailingEps" in issue for issue in result.issues)
    finally:
        client.close()


def test_partial_http_error_preserves_statistics():
    provider, client = provider_for(
        lambda r: (
            httpx.Response(403, json={"error": "plan"})
            if r.url.path.endswith("financial-data")
            else httpx.Response(200, json=envelope({"trailingEps": 4, "bookValue": 20}))
        )
    )
    try:
        result = provider.get_fundamentals(ASSET)
        assert result.eps == 4 and result.revenue is None and result.issues
    finally:
        client.close()


def test_foreign_financial_currency_is_not_combined_with_brl_statistics():
    provider, client = provider_for(
        lambda r: httpx.Response(
            200,
            json=envelope(
                {"trailingEps": 4}
                if r.url.path.endswith("statistics")
                else {"financialCurrency": "USD", "ebitda": 300}
            ),
        )
    )
    try:
        result = provider.get_fundamentals(ASSET)
        assert result.eps == 4 and result.ebitda is None and result.issues
    finally:
        client.close()


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"results": []},
        envelope([]),
        envelope({}, changed=True),
        envelope({}, symbol="PETR3"),
    ],
)
def test_invalid_or_changed_contract_has_no_invented_fundamentals(body):
    provider, client = provider_for(lambda r: httpx.Response(200, json=body))
    try:
        with pytest.raises(MarketDataError):
            provider.get_fundamentals(ASSET)
    finally:
        client.close()


def test_public_symbols_only_without_credentials():
    provider, client = provider_for(
        lambda r: pytest.fail("No HTTP for unauthorized symbol")
    )
    try:
        with pytest.raises(MarketAuthenticationError):
            provider.get_fundamentals(Asset("ABEV3"))
    finally:
        client.close()


def test_dividend_payment_window_policy_and_adjusted_rate():
    def handler(request):
        assert request.url.params["startDate"] == START.isoformat()
        assert request.url.params["endDate"] == END.isoformat()
        return httpx.Response(
            200,
            json=envelope(
                {
                    "cashDividends": [
                        {
                            "label": "DIVIDENDO",
                            "rate": "3.50",
                            "rawRate": 99,
                            "paymentDate": "2026-10-06T00:00:00.000Z",
                            "verified": True,
                        },
                        {"label": "JCP", "rate": 2, "paymentDate": "2026-01-01"},
                        {
                            "label": "DIVIDENDO",
                            "rate": 8,
                            "paymentDate": "2026-02-01",
                            "verified": False,
                        },
                        {
                            "label": "DIVIDENDO",
                            "rate": "broken",
                            "paymentDate": "2026-10-07",
                        },
                        {"label": "DIVIDENDO", "rate": 9, "paymentDate": "2025-10-06"},
                        {"label": "RENDIMENTO", "rate": 9, "paymentDate": "2026-01-01"},
                    ]
                }
            ),
        )

    provider, client = provider_for(handler)
    try:
        result = provider.get_dividends(ASSET, START, END)
        assert len(result.events) == 3
        assert annual_dividend(result) == Decimal("3.5")
        assert annual_dividend(result, include_jcp=True) == Decimal("5.5")
    finally:
        client.close()


@pytest.mark.parametrize(
    "row",
    [
        {"label": "DIVIDENDO", "rate": "broken", "paymentDate": "2026-01-01"},
        {"label": "DIVIDENDO", "rate": -1, "paymentDate": "2026-01-01"},
        {"label": "DIVIDENDO", "rate": 2, "paymentDate": None},
        {
            "label": "DIVIDENDO",
            "rate": 2,
            "paymentDate": "2026-01-01",
            "verified": "yes",
        },
    ],
)
def test_invalid_cash_event_invalidates_total_instead_of_silently_undercounting(row):
    provider, client = provider_for(
        lambda r: httpx.Response(200, json=envelope({"cashDividends": [row]}))
    )
    try:
        with pytest.raises(MarketDataUnavailableError):
            provider.get_dividends(ASSET, START, END)
    finally:
        client.close()
