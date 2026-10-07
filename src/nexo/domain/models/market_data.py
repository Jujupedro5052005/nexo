from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nexo.domain._validation import validate_decimal
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset


def _finite(value: Decimal | None, field: str) -> None:
    if value is not None and (not isinstance(value, Decimal) or not value.is_finite()):
        raise DomainValidationError(f"{field} must be finite Decimal.")


def _aware(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise DomainValidationError(f"{field} must be timezone-aware datetime.")


@dataclass(frozen=True, slots=True)
class Quote:
    asset: Asset
    price: Decimal
    currency: str
    name: str
    retrieved_at: datetime
    market_time: datetime | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    source: str = "brapi"
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    open: Decimal | None = None
    previous_close: Decimal | None = None
    volume: int | None = None
    market_cap: Decimal | None = None
    latency_ms: Decimal | None = None
    estimated_delay_minutes: int | None = None
    price_kind: str = "delayed"
    trading_date: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.asset, Asset):
            raise DomainValidationError("asset must be Asset.")
        validate_decimal(self.price, "price", positive=True)
        if not isinstance(self.currency, str):
            raise DomainValidationError("currency must be an ISO currency code.")
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
            raise DomainValidationError("currency must be an ISO currency code.")
        object.__setattr__(self, "currency", currency)
        _finite(self.change, "change")
        _finite(self.change_percent, "change_percent")
        for field in (
            "day_high",
            "day_low",
            "open",
            "previous_close",
            "market_cap",
            "latency_ms",
        ):
            _finite(getattr(self, field), field)
        if self.volume is not None and (
            type(self.volume) is not int or self.volume < 0
        ):
            raise DomainValidationError("volume must be a nonnegative integer.")
        _aware(self.retrieved_at, "retrieved_at")
        if self.market_time is not None:
            _aware(self.market_time, "market_time")

    @property
    def freshness(self) -> str:
        if self.price_kind == "eod":
            return "Fechamento diário / EOD" + (
                f" · {self.trading_date}" if self.trading_date else ""
            )
        if self.estimated_delay_minutes is not None:
            age = (
                f" · idade do dado na consulta: {self.data_age_seconds // 60} min (mercado pode estar fechado)"
                if self.data_age_seconds is not None
                else ""
            )
            return f"~{self.estimated_delay_minutes} min de atraso estimado" + age
        return "Frescor não informado"

    @property
    def data_age_seconds(self) -> int | None:
        return (
            max(0, int((self.retrieved_at - self.market_time).total_seconds()))
            if self.market_time
            else None
        )

    @property
    def symbol(self) -> str:
        return self.asset.symbol

    @property
    def current_price(self) -> Decimal:
        return self.price

    @property
    def daily_change(self) -> Decimal | None:
        return self.change

    @property
    def daily_change_percent(self) -> Decimal | None:
        return self.change_percent

    @property
    def market_timestamp(self) -> datetime | None:
        return self.market_time

    @property
    def queried_at(self) -> datetime:
        return self.retrieved_at


# Quote remains the validated snapshot consumed by valuation and UI.
MarketSnapshot = Quote


@dataclass(frozen=True, slots=True)
class HistoricalPrice:
    timestamp: datetime
    close: Decimal
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    volume: int | None = None

    def __post_init__(self) -> None:
        _aware(self.timestamp, "timestamp")
        validate_decimal(self.close, "close", positive=True)
        for field in ("open", "high", "low"):
            value = getattr(self, field)
            if value is not None:
                validate_decimal(value, field)
        if self.volume is not None and (
            type(self.volume) is not int or self.volume < 0
        ):
            raise DomainValidationError("volume must be a nonnegative integer.")


@dataclass(frozen=True, slots=True)
class PriceHistory:
    asset: Asset
    points: tuple[HistoricalPrice, ...]
    period: str
    retrieved_at: datetime
    source: str = "brapi"

    def __post_init__(self) -> None:
        if not isinstance(self.asset, Asset):
            raise DomainValidationError("asset must be Asset.")
        if not isinstance(self.points, tuple) or any(
            not isinstance(p, HistoricalPrice) for p in self.points
        ):
            raise DomainValidationError("points must be a tuple of HistoricalPrice.")
        _aware(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True)
class AssetSearchResult:
    asset: Asset
    name: str
    currency: str | None = None
    asset_type: str = ""
    source: str = "brapi"

    def __post_init__(self) -> None:
        if not isinstance(self.asset, Asset) or not isinstance(self.name, str):
            raise DomainValidationError("Search result requires Asset and name.")
        if self.currency is not None:
            if not isinstance(self.currency, str):
                raise DomainValidationError("currency must be a string.")
            object.__setattr__(self, "currency", self.currency.strip().upper())
        if not isinstance(self.asset_type, str):
            raise DomainValidationError("asset_type must be a string.")
