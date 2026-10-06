import json
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx

from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketAuthenticationError,
    MarketDataError,
    MarketDataProvider,
    MarketDataUnavailableError,
    MarketRateLimitError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import (
    AssetSearchResult,
    HistoricalPrice,
    PriceHistory,
    Quote,
)
from nexo.infrastructure.market_data.config import MarketSettings

BASE_URL = "https://brapi.dev"
PUBLIC_SYMBOLS = frozenset({"PETR4", "VALE3", "ITUB4", "MGLU3"})


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


class BrapiMarketDataProvider(MarketDataProvider):
    """All HTTP, credentials, v2 schema parsing and error translation live here."""

    def __init__(
        self,
        settings: MarketSettings | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or MarketSettings()
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(self._settings.timeout_seconds, connect=5.0),
            headers={"Accept": "application/json", "User-Agent": "Nexo-Invest/0.1"},
            follow_redirects=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _request(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
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
        except httpx.HTTPError:
            raise MarketDataUnavailableError(
                "Dados de mercado indisponíveis. Verifique sua conexão e tente novamente."
            ) from None
        if response.status_code in (401, 403):
            raise MarketAuthenticationError(
                "Autenticação ou plano sem acesso a estes dados. Confira BRAPI_TOKEN."
            )
        if response.status_code == 429:
            raise MarketRateLimitError(
                "Limite de consultas atingido. Aguarde antes de atualizar."
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
                        MarketAuthenticationError(
                            "Configure BRAPI_TOKEN para consultar este ativo."
                        ),
                    )
                )
        quotes: list[Quote] = []
        size = max(1, self._settings.batch_size)
        for offset in range(0, len(allowed), size):
            group = allowed[offset : offset + size]
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
            raise MarketAuthenticationError(
                "Configure BRAPI_TOKEN para consultar este ativo."
            )
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
