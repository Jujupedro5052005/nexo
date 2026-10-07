from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from nexo.domain.interfaces.corporate_action_provider import CorporateActionProvider
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    MarketRateLimitError,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CashDividend, DividendSummary
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory
from nexo.domain.models.official_data import CorporateAction
from nexo.infrastructure.market_data.adapters.bolsai import number
from nexo.infrastructure.market_data.policy import ProviderUsage


def yahoo_symbol(asset: Asset) -> str:
    return asset.symbol if asset.symbol.endswith(".SA") else asset.symbol + ".SA"


def _ticker(symbol: str) -> Any:
    import yfinance as yf  # type: ignore[import-untyped]  # Lazy initialization.

    return yf.Ticker(symbol)


class YahooFinanceProvider(DividendDataProvider, CorporateActionProvider):
    def __init__(
        self, usage: ProviderUsage, *, ticker_factory: Callable[[str], Any] = _ticker
    ) -> None:
        self.usage, self._ticker = usage, ticker_factory

    def _history(self, asset: Asset, operation: str, **kwargs: Any) -> Any:
        self.usage.reserve("Yahoo Finance", operation)
        try:
            frame = self._ticker(yahoo_symbol(asset)).history(
                auto_adjust=False, actions=True, raise_errors=True, timeout=10, **kwargs
            )
            if frame is None or frame.empty:
                raise ValueError("No data")
            return frame
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
