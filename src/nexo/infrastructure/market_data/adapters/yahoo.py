from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager, nullcontext
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from threading import Condition
from time import monotonic
from typing import Any, NoReturn

from nexo.core.cancellation import OperationCancelled, check_cancelled
from nexo.domain.interfaces.corporate_action_provider import CorporateActionProvider
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    MarketDataError,
    MarketDataProvider,
    MarketDataUnavailableError,
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
from nexo.domain.models.official_data import CorporateAction
from nexo.infrastructure.market_data.adapters.bolsai import number
from nexo.infrastructure.market_data.policy import ProviderUsage, explicit_refresh
from nexo.infrastructure.market_data.yahoo_transport import yahoo_request


def yahoo_symbol(asset: Asset) -> str:
    return (
        asset.symbol
        if asset.symbol.endswith(".SA")
        or asset.symbol.startswith("^")
        or "=" in asset.symbol
        or "-" in asset.symbol
        else asset.symbol + ".SA"
    )


def _ticker(symbol: str) -> Any:
    import yfinance as yf  # type: ignore[import-untyped]  # Lazy initialization.

    return yf.Ticker(symbol)


class YahooFinanceProvider(
    MarketDataProvider,
    FundamentalDataProvider,
    DividendDataProvider,
    CorporateActionProvider,
):
    def __init__(
        self,
        usage: ProviderUsage,
        *,
        ticker_factory: Callable[[str], Any] = _ticker,
        search_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.usage, self._ticker = usage, ticker_factory
        self._search = search_factory
        self._isolated = ticker_factory is _ticker
        self._info_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._info_condition = Condition()
        self._info_pending: set[str] = set()
        self._info_epoch = 0
        self._info_failures: dict[str, tuple[float, type[MarketDataError], str]] = {}

    def get_integration_status(self) -> MarketIntegrationStatus:
        return MarketIntegrationStatus(
            "Yahoo Finance",
            True,
            None,
            (),
            "Fonte principal gratuita, sem chave. Dados públicos com possível atraso, falhas ou limitação de frequência.",
        )

    def refresh_context(self, explicit: bool) -> AbstractContextManager[None]:
        return explicit_refresh() if explicit else nullcontext()

    def invalidate(self, asset: Asset | None = None) -> None:
        # Called on the GUI thread before refresh: never hold this lock over I/O.
        with self._info_condition:
            self._info_epoch += 1
            if asset is None:
                self._info_cache.clear()
                self._info_failures.clear()
            else:
                self._info_cache.pop(asset.symbol, None)
                self._info_failures.pop(asset.symbol, None)

    def _info(self, asset: Asset) -> dict[str, Any]:
        symbol = asset.symbol
        with self._info_condition:
            while symbol in self._info_pending:
                self._info_condition.wait(timeout=0.1)
                check_cancelled()
            cached = self._info_cache.get(symbol)
            if cached and cached[0] > monotonic():
                return cached[1]
            failure = self._info_failures.get(symbol)
            if failure and failure[0] > monotonic():
                raise failure[1](failure[2])
            self._info_pending.add(symbol)
            epoch = self._info_epoch
        reserved = False
        try:
            self.usage.reserve("Yahoo Finance", "snapshot")
            reserved = True
            try:
                info = (
                    yahoo_request(yahoo_symbol(asset), "get_info")
                    if self._isolated
                    else self._ticker(yahoo_symbol(asset)).get_info()
                )
                if not isinstance(info, dict) or not info:
                    raise ValueError("Empty snapshot")
            except Exception as error:  # noqa: BLE001 -- normalize third-party errors.
                self._raise_error(error)
            with self._info_condition:
                if epoch == self._info_epoch:
                    self._info_cache[symbol] = (monotonic() + 60, info)
                    while len(self._info_cache) > 256:
                        self._info_cache.pop(next(iter(self._info_cache)))
            return info
        except MarketDataError as error:
            with self._info_condition:
                if reserved and epoch == self._info_epoch:
                    self._info_failures[symbol] = (
                        monotonic() + 30,
                        type(error),
                        str(error),
                    )
                    while len(self._info_failures) > 256:
                        self._info_failures.pop(next(iter(self._info_failures)))
            raise
        finally:
            with self._info_condition:
                self._info_pending.discard(symbol)
                self._info_condition.notify_all()

    @staticmethod
    def _raise_error(error: Exception) -> NoReturn:
        if isinstance(error, (OperationCancelled, MarketDataError)):
            raise error
        from yfinance.exceptions import YFRateLimitError  # type: ignore[import-untyped]

        if isinstance(error, YFRateLimitError):
            raise MarketRateLimitError(
                "Yahoo Finance: limite remoto atingido."
            ) from None
        raise MarketDataUnavailableError(
            "Yahoo Finance: dados temporariamente indisponíveis."
        ) from None

    @staticmethod
    def _timestamp(value: Any) -> datetime | None:
        try:
            return (
                datetime.fromtimestamp(value, timezone.utc)
                if value and not isinstance(value, bool)
                else None
            )
        except (ValueError, TypeError, OverflowError, OSError):
            return None

    def get_quote(self, asset: Asset) -> Quote:
        return self._quote_from_info(asset, self._info(asset))

    def _quote_from_info(self, asset: Asset, info: dict[str, Any]) -> Quote:
        def optional(key: str) -> Decimal | None:
            try:
                return number(info.get(key))
            except (ValueError, TypeError, ArithmeticError):
                return None

        volume = optional("regularMarketVolume")
        try:
            price = number(info.get("regularMarketPrice"))
            if price is None or price <= 0 or not info.get("currency"):
                raise ValueError("Missing price/currency")
            return Quote(
                asset,
                price,
                info["currency"],
                info.get("longName") or info.get("shortName") or asset.symbol,
                datetime.now(timezone.utc),
                market_time=self._timestamp(info.get("regularMarketTime")),
                source="Yahoo Finance",
                change=optional("regularMarketChange"),
                change_percent=optional("regularMarketChangePercent"),
                day_high=optional("regularMarketDayHigh"),
                day_low=optional("regularMarketDayLow"),
                open=optional("regularMarketOpen"),
                previous_close=optional("regularMarketPreviousClose"),
                volume=int(volume)
                if volume is not None
                and volume >= 0
                and volume == volume.to_integral_value()
                else None,
                market_cap=optional("marketCap"),
            )
        except (ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError(
                "Cotação Yahoo inválida ou incompleta."
            ) from None

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        requested = tuple(dict.fromkeys(assets))
        if not requested:
            return QuoteBatch(())
        if not self._isolated:
            # Injected SDK fakes preserve the standalone adapter contract.
            quotes, issues = [], []
            for asset in requested:
                try:
                    quotes.append(self.get_quote(asset))
                except MarketDataError as error:
                    issues.append(QuoteIssue(asset, error))
            return QuoteBatch(tuple(quotes), tuple(issues))
        self.usage.reserve("Yahoo Finance", "quotes")
        data = yahoo_request(
            "", "quotes", symbols=tuple(yahoo_symbol(a) for a in requested)
        )
        quotes, issues = [], []
        for asset in requested:
            try:
                info = data.get(yahoo_symbol(asset))
                if not isinstance(info, dict):
                    raise MarketDataUnavailableError(
                        "Cotação Yahoo indisponível para este ativo."
                    )
                quotes.append(self._quote_from_info(asset, info))
            except MarketDataError as error:
                issues.append(QuoteIssue(asset, error))
        return QuoteBatch(tuple(quotes), tuple(issues))

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:

        self.usage.reserve("Yahoo Finance", "search")
        try:
            results = (
                self._search(query.strip())
                if self._search
                else yahoo_request(query.strip(), "search")
            )
            return tuple(
                AssetSearchResult(
                    Asset(row["symbol"].removesuffix(".SA")),
                    row.get("longname") or row.get("shortname") or row["symbol"],
                    "BRL",
                    row.get("quoteType", ""),
                    "Yahoo Finance",
                )
                for row in results
                if row.get("symbol", "").endswith(".SA")
            )
        except Exception as error:  # noqa: BLE001 -- normalize third-party errors.
            self._raise_error(error)

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        info = self._info(asset)
        # Never treat accounting values reported in another currency as BRL.
        if info.get("financialCurrency") != "BRL" or info.get("currency") != "BRL":
            raise MarketDataUnavailableError(
                "Fundamentos Yahoo sem base monetária BRL confirmada."
            )
        mapping = {
            "eps": "trailingEps",
            "bvps": "bookValue",
            "roe": "returnOnEquity",
            "roa": "returnOnAssets",
            "net_margin": "profitMargins",
            "revenue": "totalRevenue",
            "ebitda": "ebitda",
            "debt": "totalDebt",
            "cash": "totalCash",
            "gross_margin": "grossMargins",
            "current_ratio": "currentRatio",
            "market_cap": "marketCap",
            "net_income": "netIncomeToCommon",
            "ebitda_margin": "ebitdaMargins",
        }
        values: dict[str, Any] = {}
        for field, key in mapping.items():
            try:
                values[field] = number(info.get(key))
            except (ValueError, TypeError, ArithmeticError):
                values[field] = None
        timestamp = self._timestamp(info.get("mostRecentQuarter"))
        return CompanyFundamentals(
            asset,
            datetime.now(timezone.utc),
            source="Yahoo Finance",
            reference_date=timestamp.date() if timestamp else None,
            issues=(
                "Yahoo: LPA/receita/EBITDA são bases TTM; VPA é o último balanço. Campos ausentes não são zero.",
            ),
            **values,
        )

    def _history(self, asset: Asset, operation: str, **kwargs: Any) -> Any:
        self.usage.reserve("Yahoo Finance", operation)
        try:
            options = dict(
                auto_adjust=False, actions=True, raise_errors=True, timeout=10, **kwargs
            )
            frame = (
                yahoo_request(yahoo_symbol(asset), "history", **options)
                if self._isolated
                else self._ticker(yahoo_symbol(asset)).history(**options)
            )
            if frame is None or frame.empty:
                raise ValueError("No data")
            return frame
        except OperationCancelled:
            raise
        except Exception as error:  # noqa: BLE001 -- yfinance exposes heterogeneous transport errors.
            from yfinance.exceptions import (  # type: ignore[import-untyped]
                YFRateLimitError,
            )

            if isinstance(error, YFRateLimitError):
                raise MarketRateLimitError(
                    "Yahoo Finance: limite remoto atingido."
                ) from None
            raise MarketDataUnavailableError(
                "Yahoo Finance: dados temporariamente indisponíveis."
            ) from None

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        if period not in {"1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"}:
            raise MarketDataUnavailableError("Período não suportado.")
        frame = self._history(asset, "history", period=period)
        return self.normalize_history(asset, period, frame)

    @staticmethod
    def normalize_history(asset: Asset, period: str, frame: Any) -> PriceHistory:
        try:
            points = []
            for index, row in frame.iterrows():
                timestamp = index.to_pydatetime()
                if timestamp.utcoffset() is None:
                    raise ValueError("Missing timezone")
                close = number(row.get("Close"))
                if close is None:
                    raise ValueError("Missing close")

                def optional(field: str, row: Any = row) -> Decimal | None:
                    try:
                        return number(row.get(field))
                    except (ValueError, ArithmeticError):
                        return None

                volume = optional("Volume")
                points.append(
                    HistoricalPrice(
                        timestamp,
                        close,
                        optional("Open"),
                        optional("High"),
                        optional("Low"),
                        int(volume) if volume is not None else None,
                    )
                )
            return PriceHistory(
                asset,
                tuple(sorted(points, key=lambda p: p.timestamp)),
                period,
                datetime.now(timezone.utc),
                "Yahoo Finance",
                splits=tuple(
                    (index.to_pydatetime(), ratio)
                    for index, row in frame.iterrows()
                    if (ratio := number(row.get("Stock Splits"))) is not None
                    and ratio > 0
                ),
                split_adjusted=True,
            )
        except (ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError("Histórico Yahoo inválido.") from None

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        frame = self._history(
            asset,
            "dividends",
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
        )
        return self.normalize_dividends(asset, start_date, end_date, frame)

    @staticmethod
    def normalize_dividends(
        asset: Asset, start_date: date, end_date: date, frame: Any
    ) -> DividendSummary:
        limitations = (
            "Yahoo não distingue dividendo/JCP; tipo CASH_DISTRIBUTION preservado.",
            "Data de pagamento indisponível; janela usa data-ex.",
        )
        try:
            events = tuple(
                CashDividend(
                    None,
                    amount,
                    "CASH_DISTRIBUTION",
                    None,
                    asset,
                    index.date(),
                    "BRL",
                    "Yahoo Finance",
                    limitations,
                )
                for index, row in frame.iterrows()
                if (amount := number(row.get("Dividends"))) is not None
                and amount > 0
                and start_date <= index.date() <= end_date
            )
            return DividendSummary(
                asset,
                events,
                start_date,
                end_date,
                datetime.now(timezone.utc),
                source="Yahoo Finance",
                date_basis="ex_date",
                limitations=limitations,
            )
        except (ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError("Proventos Yahoo inválidos.") from None

    def get_actions(self, asset: Asset) -> tuple[CorporateAction, ...]:
        frame = self._history(asset, "actions", period="max")
        try:
            return tuple(
                CorporateAction(asset.symbol, index.date(), ratio, "Yahoo Finance")
                for index, row in frame.iterrows()
                if (ratio := number(row.get("Stock Splits"))) is not None and ratio > 0
            )
        except (ValueError, TypeError, ArithmeticError):
            raise MarketDataUnavailableError("Splits Yahoo inválidos.") from None
