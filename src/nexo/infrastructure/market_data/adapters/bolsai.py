import json
from collections.abc import Iterable
from datetime import date, datetime, timezone
from decimal import Decimal
from time import perf_counter
from typing import Any

import httpx

from nexo.calculations.precision import financial_context
from nexo.domain.interfaces.corporate_action_provider import CorporateActionProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketCredentialsRequiredError,
    MarketDataError,
    MarketDataProvider,
    MarketDataUnavailableError,
    MarketInvalidTokenError,
    MarketOfflineError,
    MarketPlanAccessError,
    MarketRateLimitError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.domain.models.official_data import CompanyIdentity, CorporateAction
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.infrastructure.market_data.policy import ProviderPolicy

BASE_URL = "https://api.usebolsai.com/api/v1"


def number(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("Boolean is not a financial amount")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Nonfinite amount")
    return result


class BolsaiProvider(
    MarketDataProvider, FundamentalDataProvider, CorporateActionProvider
):
    def __init__(
        self,
        settings: MarketSettings,
        policy: ProviderPolicy,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings, self.policy = settings, policy
        self._owns_client = client is None
        self.client = client or httpx.Client(
            timeout=settings.timeout_seconds, follow_redirects=False
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _request(
        self, path: str, operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self.settings.bolsai_api_key:
            raise MarketCredentialsRequiredError(
                "bolsai não configurada: defina BOLSAI_API_KEY."
            )
        if self.policy.quota_remaining("bolsai") == 0:
            raise MarketRateLimitError(
                "Quota bolsai esgotada segundo header; reset 00:00 UTC."
            )
        self.policy.usage.reserve("bolsai", operation)
        try:
            response = self.client.get(
                BASE_URL + path,
                params=params,
                headers={"X-API-Key": self.settings.bolsai_api_key},
            )
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining and remaining.isdigit():
                self.policy.update_quota("bolsai", int(remaining))
            errors: dict[int, tuple[type[MarketDataError], str]] = {
                401: (MarketInvalidTokenError, "Chave bolsai não aceita (HTTP 401)."),
                403: (MarketPlanAccessError, "Recurso bolsai restrito pelo plano (HTTP 403)."),
                404: (AssetNotFoundError, "Dados não encontrados na bolsai (HTTP 404)."),
                429: (MarketRateLimitError, "Limite de consultas bolsai atingido (HTTP 429)."),
            }
            if response.status_code in errors:
                error_type, message = errors[response.status_code]
                raise error_type(message)
            if response.status_code != 200:
                raise MarketDataUnavailableError(
                    f"bolsai: resposta HTTP {response.status_code}. Tente novamente mais tarde."
                )
            payload = json.loads(response.text, parse_float=Decimal)
            if not isinstance(payload, dict):
                raise TypeError("Expected object")
            return payload
        except httpx.ConnectError:
            raise MarketOfflineError("bolsai offline. Verifique sua conexão.") from None
        except httpx.TimeoutException:
            raise MarketDataUnavailableError(
                "bolsai: tempo limite de resposta excedido. Tente novamente."
            ) from None
        except (httpx.HTTPError, ValueError, TypeError):
            raise MarketDataUnavailableError(
                "bolsai: resposta indisponível ou inválida."
            ) from None

    def get_company_identity(self, asset: Asset) -> CompanyIdentity:
        def fetch() -> CompanyIdentity:
            row = self._request(f"/companies/{asset.symbol}", "company")
            try:
                queried = row.get("queried_ticker", asset.symbol)
                tickers = tuple(row.get("tickers", [row["ticker_primary"]]))
                if queried != asset.symbol or asset.symbol not in tickers:
                    raise ValueError("Identity mismatch")
                return CompanyIdentity(
                    row["ticker_primary"],
                    queried,
                    tickers,
                    row["corporate_name"],
                    row.get("trade_name", ""),
                    str(int(row["cvm_code"])),
                    "".join(c for c in row["cnpj"] if c.isdigit()),
                    row.get("sector", ""),
                    row.get("status", ""),
                )
            except (KeyError, ValueError, TypeError):
                raise MarketDataUnavailableError(
                    "Identidade oficial não resolvida."
                ) from None

        return self.policy.call("bolsai", "company", (asset,), fetch)

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        quotes, issues = [], []
        for asset in dict.fromkeys(assets):
            try:
                started = perf_counter()
                row = self._request(f"/stocks/{asset.symbol}/quote", "quote")
                if row.get("ticker") != asset.symbol:
                    raise ValueError("Ticker mismatch")
                price = number(row["close"])
                if price is None:
                    raise ValueError("Missing close")
                trading_date = date.fromisoformat(row["trade_date"]).isoformat()
                quotes.append(
                    Quote(
                        asset,
                        price,
                        "BRL",
                        row.get("corporate_name", asset.symbol),
                        datetime.now(timezone.utc),
                        source="bolsai",
                        change=number(row.get("daily_change")),
                        change_percent=number(row.get("daily_change_pct")),
                        day_high=number(row.get("high")),
                        day_low=number(row.get("low")),
                        open=number(row.get("open")),
                        previous_close=number(row.get("previous_close")),
                        volume=row.get("volume"),
                        market_cap=number(row.get("market_cap")),
                        latency_ms=Decimal(str((perf_counter() - started) * 1000)),
                        price_kind="eod",
                        trading_date=trading_date,
                    )
                )
            except MarketDataError as error:
                issues.append(QuoteIssue(asset, error))
            except (KeyError, ValueError, TypeError, ArithmeticError):
                issues.append(
                    QuoteIssue(
                        asset, MarketDataUnavailableError("Snapshot bolsai inválido.")
                    )
                )
        return QuoteBatch(tuple(quotes), tuple(issues))

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        rows = self._request(
            "/companies", "search", {"search": query, "limit": 20}
        ).get("data")
        try:
            if not isinstance(rows, list):
                raise TypeError("Expected companies")
            return tuple(
                AssetSearchResult(
                    Asset(row["ticker_primary"]),
                    row["corporate_name"],
                    "BRL",
                    "stock",
                    "bolsai",
                )
                for row in rows
                if row.get("ticker_primary")
            )
        except (KeyError, ValueError, TypeError, AttributeError):
            raise MarketDataUnavailableError("Busca bolsai inválida.") from None

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        raise MarketPlanAccessError(
            "Histórico bolsai não é consumido neste incremento."
        )

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        row = self._request(f"/fundamentals/{asset.symbol}", "fundamentals")
        if row.get("queried_ticker", row.get("ticker")) != asset.symbol:
            raise MarketDataUnavailableError(
                "Fundamentos de outra classe de ação recusados."
            )
        mapping = {
            "eps": "lpa",
            "bvps": "vpa",
            "pe": "pl",
            "pb": "pvp",
            "ev_ebitda": "ev_ebitda",
            "roe": "roe",
            "roa": "roa",
            "roic": "roic",
            "net_margin": "net_margin",
            "gross_margin": "gross_margin",
            "ebitda_margin": "ebitda_margin",
            "debt_equity": "debt_equity",
            "net_debt_ebitda": "net_debt_ebitda",
            "current_ratio": "current_ratio",
            "market_cap": "market_cap",
            "revenue": "net_revenue",
            "net_income": "net_income",
            "equity": "equity",
            "debt": "total_debt",
            "cash": "cash",
            "total_assets": "total_assets",
            "ebit": "ebit",
            "ebitda": "ebitda",
        }
        ratios = {"roe", "roa", "roic", "net_margin", "gross_margin", "ebitda_margin"}
        values: dict[str, Any] = {}
        issues = []
        for target, field in mapping.items():
            try:
                value = number(row.get(field))
                values[target] = (
                    value.scaleb(-2, context=financial_context([value]))
                    if value is not None and target in ratios
                    else value
                )
            except (ValueError, TypeError, ArithmeticError):
                values[target] = None
                issues.append(f"bolsai.{field}: campo inválido.")
        reference = None
        try:
            if row.get("reference_date"):
                reference = date.fromisoformat(row["reference_date"])
        except ValueError:
            issues.append("Referência contábil inválida.")
        return CompanyFundamentals(
            asset,
            datetime.now(timezone.utc),
            reference_date=reference,
            source="bolsai",
            issues=tuple(issues),
            **values,
        )

    def get_actions(self, asset: Asset) -> tuple[CorporateAction, ...]:
        row = self._request(f"/stocks/{asset.symbol}/corporate-events", "actions")
        try:
            return tuple(
                CorporateAction(
                    asset.symbol,
                    date.fromisoformat(e["date"]),
                    Decimal(str(e["ratio_to"])) / Decimal(str(e["ratio_from"])),
                    "bolsai",
                )
                for e in row["events"]
            )
        except (KeyError, ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError(
                "Eventos corporativos bolsai inválidos."
            ) from None
