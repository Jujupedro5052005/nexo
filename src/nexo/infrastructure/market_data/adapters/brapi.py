import json
from collections.abc import Iterable
from contextlib import AbstractContextManager, nullcontext
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from time import perf_counter
from typing import Any

import httpx

from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
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
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.market_data import (
    AssetSearchResult,
    HistoricalPrice,
    PriceHistory,
    Quote,
)
from nexo.domain.models.market_integration import MarketIntegrationStatus
from nexo.infrastructure.market_data.config import PUBLIC_SYMBOLS, MarketSettings
from nexo.infrastructure.market_data.policy import ProviderUsage, explicit_refresh

BASE_URL = "https://brapi.dev"


def _invalid_constant(_value: str) -> None:
    raise ValueError("Nonfinite JSON number")


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise TypeError("Invalid decimal field")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("Invalid decimal field")
    return result


def _optional_decimal(value: Any) -> Decimal | None:
    return None if value is None else _decimal(value)


def _timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.utcoffset() is None:
            raise ValueError("Timestamp requires an offset")
        return result
    if isinstance(value, (int, Decimal)) and not isinstance(value, bool):
        seconds = _decimal(value)
        whole = int(seconds)
        micros = int((seconds - whole) * Decimal(1000000))
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
            seconds=whole, microseconds=micros
        )
    raise ValueError("Invalid timestamp")


class BrapiMarketDataProvider(
    MarketDataProvider, FundamentalDataProvider, DividendDataProvider
):
    """All HTTP, credentials, v2 schema parsing and error translation live here."""

    def __init__(
        self,
        settings: MarketSettings | None = None,
        *,
        client: httpx.Client | None = None,
        usage: ProviderUsage | None = None,
    ) -> None:
        self._settings = settings or MarketSettings()
        self._usage = usage
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(self._settings.timeout_seconds, connect=5.0),
            headers={"Accept": "application/json", "User-Agent": "Nexo-Invest/0.1"},
            follow_redirects=False,
        )

    def get_integration_status(self) -> MarketIntegrationStatus:
        configured = bool(self._settings.token)
        status = MarketIntegrationStatus("brapi", configured, None, PUBLIC_SYMBOLS, "")
        return MarketIntegrationStatus(
            "brapi",
            configured,
            None,
            PUBLIC_SYMBOLS,
            "Chave configurada. A autenticação ainda não foi verificada."
            if configured
            else status.public_access_description + " " + status.configuration_guidance,
        )

    def _credentials_required_message(self) -> str:
        status = self.get_integration_status()
        return status.public_access_description + " " + status.configuration_guidance

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def refresh_context(self, explicit: bool) -> AbstractContextManager[None]:
        return explicit_refresh() if explicit else nullcontext()

    def _request(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        if self._usage is not None:
            operation = (
                "quote"
                if path.endswith("quote")
                else "history"
                if path.endswith("historical")
                else "search"
                if path.endswith("tickers")
                else "dividends"
                if path.endswith("dividends")
                else "fundamentals"
            )
            self._usage.reserve("brapi", operation)
        headers = (
            {"Authorization": f"Bearer {self._settings.token}"}
            if self._settings.token
            else {}
        )
        try:
            response = self._client.get(
                BASE_URL + path,
                params=params,
                headers=headers,
                timeout=self._settings.timeout_seconds,
            )
        except httpx.ConnectError:
            raise MarketOfflineError("brapi offline. Verifique sua conexão.") from None
        except httpx.HTTPError:
            raise MarketDataUnavailableError(
                "Não foi possível acessar a brapi. Verifique sua conexão."
            ) from None
        if response.status_code == 401:
            raise MarketInvalidTokenError(
                "A chave configurada não foi aceita pela brapi."
            )
        if response.status_code == 403:
            raise MarketPlanAccessError(
                "Este recurso não está disponível no plano atual da brapi."
            )
        if response.status_code == 429:
            raise MarketRateLimitError(
                "O limite de consultas foi atingido. Tente novamente mais tarde."
            )
        if response.status_code == 404:
            raise AssetNotFoundError("Ativo sem dados disponíveis na brapi.")
        if response.status_code != 200:
            raise MarketDataUnavailableError(
                "A brapi não disponibilizou os dados solicitados. Confira o período e os limites do plano."
            )
        try:
            payload = json.loads(
                response.text, parse_float=Decimal, parse_constant=_invalid_constant
            )
            if not isinstance(payload, dict) or not isinstance(
                payload.get("results"), list
            ):
                raise TypeError("Unexpected response")
            return payload
        except (ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError(
                "Resposta de mercado inválida ou incompleta."
            ) from None

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        requested = list(dict.fromkeys(assets))
        issues: list[QuoteIssue] = []
        allowed = []
        for asset in requested:
            if self._settings.token or asset.symbol in PUBLIC_SYMBOLS:
                allowed.append(asset)
            else:
                issues.append(
                    QuoteIssue(
                        asset,
                        MarketCredentialsRequiredError(
                            self._credentials_required_message()
                        ),
                    )
                )
        quotes: list[Quote] = []
        size = max(1, self._settings.batch_size)
        for offset in range(0, len(allowed), size):
            group = allowed[offset : offset + size]
            started = perf_counter()
            try:
                payload = self._request(
                    "/api/v2/stocks/quote",
                    {"symbols": ",".join(a.symbol for a in group)},
                )
                retrieved_at = datetime.now(timezone.utc)
                records = {}
                for row in payload["results"]:
                    if isinstance(row, dict) and isinstance(
                        row.get("requestedSymbol") or row.get("symbol"), str
                    ):
                        records[Asset(row.get("requestedSymbol") or row["symbol"])] = (
                            row
                        )
            except MarketDataError as error:
                issues.extend(QuoteIssue(asset, error) for asset in group)
                continue
            except (ValueError, KeyError, TypeError):
                issues.extend(
                    QuoteIssue(
                        asset,
                        MarketDataUnavailableError("Resposta de mercado inválida."),
                    )
                    for asset in group
                )
                continue
            for asset in group:
                try:
                    row = records.get(asset)
                    if row is None:
                        issues.append(
                            QuoteIssue(
                                asset,
                                AssetNotFoundError("Ativo sem cotação disponível."),
                            )
                        )
                        continue
                    if Asset(row["symbol"]) != asset or row.get("changed"):
                        issues.append(
                            QuoteIssue(
                                asset,
                                MarketDataUnavailableError(
                                    "Ticker alterado; conversões de ações não são aplicadas ao ledger automaticamente."
                                ),
                            )
                        )
                        continue
                    data = row["data"]
                    quotes.append(
                        Quote(
                            asset=asset,
                            price=_decimal(data["regularMarketPrice"]),
                            currency=data["currency"],
                            name=data.get("longName")
                            or data.get("shortName")
                            or asset.symbol,
                            retrieved_at=retrieved_at,
                            market_time=_timestamp(data["regularMarketTime"])
                            if data.get("regularMarketTime") is not None
                            else None,
                            change=_optional_decimal(data.get("regularMarketChange")),
                            change_percent=_optional_decimal(
                                data.get("regularMarketChangePercent")
                            ),
                            day_high=_optional_decimal(
                                data.get("regularMarketDayHigh")
                            ),
                            day_low=_optional_decimal(data.get("regularMarketDayLow")),
                            open=_optional_decimal(data.get("regularMarketOpen")),
                            previous_close=_optional_decimal(
                                data.get("regularMarketPreviousClose")
                            ),
                            volume=data.get("regularMarketVolume"),
                            market_cap=_optional_decimal(data.get("marketCap")),
                            latency_ms=Decimal(str((perf_counter() - started) * 1000)),
                            estimated_delay_minutes=30,
                        )
                    )
                except (
                    ValueError,
                    ArithmeticError,
                    KeyError,
                    TypeError,
                    AttributeError,
                    OverflowError,
                ):
                    issues.append(
                        QuoteIssue(
                            asset,
                            MarketDataUnavailableError(
                                "Cotação inválida ou incompleta."
                            ),
                        )
                    )
        return QuoteBatch(tuple(quotes), tuple(issues))

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        payload = self._request(
            "/api/v2/tickers",
            {
                "search": query.strip(),
                "limit": 20,
                "sortBy": "symbol",
                "sortOrder": "asc",
            },
        )
        try:
            return tuple(
                AssetSearchResult(
                    Asset(row["symbol"]),
                    row.get("longName") or row.get("name") or row["symbol"],
                    row.get("currency"),
                    row.get("assetType", ""),
                )
                for row in payload["results"]
            )
        except (ValueError, KeyError, TypeError, AttributeError):
            raise MarketDataUnavailableError("Resultado de busca inválido.") from None

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        if period not in {"1mo", "3mo", "1y"}:
            raise MarketDataUnavailableError("Período não suportado nesta versão.")
        if not self._settings.token and asset.symbol not in PUBLIC_SYMBOLS:
            raise MarketCredentialsRequiredError(self._credentials_required_message())
        payload = self._request(
            "/api/v2/stocks/historical",
            {
                "symbols": asset.symbol,
                "range": period,
                "interval": "1d",
                "sortOrder": "asc",
            },
        )
        try:
            row = next(
                (
                    r
                    for r in payload["results"]
                    if (r.get("requestedSymbol") or r.get("symbol")) == asset.symbol
                ),
                None,
            )
            if row is None:
                raise AssetNotFoundError("Histórico não disponível para este ativo.")
            if Asset(row["symbol"]) != asset or row.get("changed"):
                raise MarketDataUnavailableError(
                    "Ticker alterado; histórico do substituto não é exibido como ativo original."
                )
            points = tuple(
                sorted(
                    (
                        HistoricalPrice(
                            timestamp=_timestamp(point["date"]),
                            close=_decimal(point["close"]),
                            open=_optional_decimal(point.get("open")),
                            high=_optional_decimal(point.get("high")),
                            low=_optional_decimal(point.get("low")),
                            volume=point.get("volume"),
                        )
                        for point in row["data"]["historicalDataPrice"]
                    ),
                    key=lambda point: point.timestamp,
                )
            )
            return PriceHistory(asset, points, period, datetime.now(timezone.utc))
        except MarketDataError:
            raise
        except (
            ValueError,
            ArithmeticError,
            KeyError,
            TypeError,
            AttributeError,
            OverflowError,
        ):
            raise MarketDataUnavailableError(
                "Histórico de preços inválido ou incompleto."
            ) from None

    def _company_data(
        self, path: str, asset: Asset, params: dict[str, str | int] | None = None
    ) -> Any:
        if not self._settings.token and asset.symbol not in PUBLIC_SYMBOLS:
            raise MarketCredentialsRequiredError(self._credentials_required_message())
        payload = self._request(path, {"symbols": asset.symbol, **(params or {})})
        try:
            row = next(
                (
                    r
                    for r in payload["results"]
                    if isinstance(r, dict)
                    and (r.get("requestedSymbol") or r.get("symbol")) == asset.symbol
                ),
                None,
            )
            if row is None:
                raise AssetNotFoundError(
                    "Dados analíticos não disponíveis para este ativo."
                )
            if Asset(row["symbol"]) != asset or row.get("changed"):
                raise MarketDataUnavailableError(
                    "Ticker alterado: confirme o ativo para obter análise compatível."
                )
            if not isinstance(row["data"], dict):
                raise TypeError("Expected company object")
            return row["data"]
        except (ValueError, KeyError, TypeError, AttributeError):
            raise MarketDataUnavailableError(
                "Formato de dados analíticos inválido."
            ) from None

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        issues: list[str] = []
        modules: list[dict[str, Any]] = []
        errors: list[MarketDataError] = []
        for endpoint in ("statistics", "financial-data"):
            try:
                modules.append(
                    self._company_data(
                        f"/api/v2/stocks/{endpoint}", asset, {"mode": "current"}
                    )
                )
            except MarketDataError as error:
                modules.append({})
                errors.append(error)
                issues.append(f"{endpoint}: {error}")
        if len(errors) == 2:
            raise errors[0]
        statistics, financial = modules
        if financial.get("financialCurrency") not in (None, "BRL"):
            issues.append(
                "Moeda financeira incompatível com o escopo BRL; dados desse módulo indisponíveis."
            )
            financial = {}

        def number(data: dict[str, Any], field: str) -> Decimal | None:
            try:
                return _optional_decimal(data.get(field))
            except (ValueError, TypeError, ArithmeticError):
                issues.append(f"Campo {field} inválido; indisponível.")
                return None

        reference = None
        if statistics.get("mostRecentQuarter") is not None:
            try:
                reference = date.fromisoformat(
                    str(statistics["mostRecentQuarter"])[:10]
                )
            except ValueError:
                issues.append("Referência contábil não informada em formato válido.")
        eps = number(statistics, "trailingEps")
        if eps is None:
            eps = number(statistics, "earningsPerShare")
        return CompanyFundamentals(
            asset=asset,
            retrieved_at=datetime.now(timezone.utc),
            eps=eps,
            bvps=number(statistics, "bookValue"),
            roe=number(financial, "returnOnEquity"),
            roa=number(financial, "returnOnAssets"),
            net_margin=number(financial, "profitMargins"),
            revenue=number(financial, "totalRevenue"),
            ebitda=number(financial, "ebitda"),
            debt=number(financial, "totalDebt"),
            cash=number(financial, "totalCash"),
            reference_date=reference,
            issues=tuple(issues),
        )

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        data = self._company_data(
            "/api/v2/stocks/dividends",
            asset,
            {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "sortOrder": "asc",
            },
        )
        try:
            rows = data["cashDividends"]
            if not isinstance(rows, list):
                raise TypeError("Expected cash distributions")
            events = []
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("label"), str):
                    raise TypeError("Invalid distribution")
                kind = row["label"].strip().upper()
                if kind not in {"DIVIDENDO", "JCP"}:
                    continue
                raw_date = row["paymentDate"]
                payment = (
                    date.fromisoformat(raw_date)
                    if isinstance(raw_date, str) and len(raw_date) == 10
                    else _timestamp(raw_date).date()
                )
                if start_date <= payment <= end_date:
                    events.append(
                        CashDividend(
                            payment, _decimal(row["rate"]), kind, row.get("verified")
                        )
                    )
            events.sort(key=lambda e: e.payment_date or date.min)
            return DividendSummary(
                asset, tuple(events), start_date, end_date, datetime.now(timezone.utc)
            )
        except (
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            ArithmeticError,
            OverflowError,
        ):
            raise MarketDataUnavailableError(
                "Proventos inválidos ou incompletos; total anual indisponível."
            ) from None
