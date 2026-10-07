from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from nexo.domain._validation import validate_decimal
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import _aware, _finite


@dataclass(frozen=True, slots=True)
class CompanyFundamentals:
    asset: Asset
    retrieved_at: datetime
    eps: Decimal | None = None
    bvps: Decimal | None = None
    roe: Decimal | None = None
    roa: Decimal | None = None
    net_margin: Decimal | None = None
    revenue: Decimal | None = None
    ebitda: Decimal | None = None
    debt: Decimal | None = None
    cash: Decimal | None = None
    reference_date: date | None = None
    currency: str = "BRL"
    source: str = "brapi"
    issues: tuple[str, ...] = ()
    pe: Decimal | None = None
    pb: Decimal | None = None
    ev_ebitda: Decimal | None = None
    roic: Decimal | None = None
    gross_margin: Decimal | None = None
    ebitda_margin: Decimal | None = None
    debt_equity: Decimal | None = None
    net_debt_ebitda: Decimal | None = None
    current_ratio: Decimal | None = None
    market_cap: Decimal | None = None
    net_income: Decimal | None = None
    equity: Decimal | None = None
    total_assets: Decimal | None = None
    ebit: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.asset, Asset):
            raise DomainValidationError("asset must be Asset.")
        _aware(self.retrieved_at, "retrieved_at")
        for field in (
            "eps",
            "bvps",
            "roe",
            "roa",
            "net_margin",
            "revenue",
            "ebitda",
            "debt",
            "cash",
            "pe",
            "pb",
            "ev_ebitda",
            "roic",
            "gross_margin",
            "ebitda_margin",
            "debt_equity",
            "net_debt_ebitda",
            "current_ratio",
            "market_cap",
            "net_income",
            "equity",
            "total_assets",
            "ebit",
        ):
            _finite(getattr(self, field), field)
        if self.currency != "BRL":
            raise DomainValidationError("This fundamental snapshot supports BRL only.")


@dataclass(frozen=True, slots=True)
class CashDividend:
    payment_date: date | None
    amount: Decimal
    kind: str
    verified: bool | None = None
    asset: Asset | None = None
    ex_date: date | None = None
    currency: str = "BRL"
    source: str = "brapi"
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.payment_date is not None and type(self.payment_date) is not date:
            raise DomainValidationError("payment_date must be date.")
        validate_decimal(self.amount, "amount")
        if self.kind not in {"DIVIDENDO", "JCP", "CASH_DISTRIBUTION"}:
            raise DomainValidationError("Unsupported dividend kind.")
        if self.verified is not None and type(self.verified) is not bool:
            raise DomainValidationError("verified must be boolean or absent.")

    @property
    def event_type(self) -> str:
        return self.kind

    @property
    def amount_per_share(self) -> Decimal:
        return self.amount


@dataclass(frozen=True, slots=True)
class DividendSummary:
    asset: Asset
    events: tuple[CashDividend, ...]
    start_date: date
    end_date: date
    retrieved_at: datetime
    currency: str = "BRL"
    source: str = "brapi"
    date_basis: str = "payment_date"
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.asset, Asset)
            or not isinstance(self.events, tuple)
            or any(not isinstance(e, CashDividend) for e in self.events)
        ):
            raise DomainValidationError("Invalid dividend snapshot.")
        if (
            type(self.start_date) is not date
            or type(self.end_date) is not date
            or self.start_date > self.end_date
        ):
            raise DomainValidationError("Invalid dividend window.")
        _aware(self.retrieved_at, "retrieved_at")
        if self.currency != "BRL":
            raise DomainValidationError("Dividend snapshot supports BRL only.")
