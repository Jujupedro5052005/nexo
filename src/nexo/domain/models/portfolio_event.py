from dataclasses import dataclass
from datetime import datetime
from decimal import Context, Decimal, localcontext
from enum import Enum

from nexo.domain._validation import validate_decimal, validate_identity
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset


class PortfolioEventType(str, Enum):
    OPENING = "OPENING"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    JCP = "JCP"
    FEE = "FEE"
    TAX = "TAX"
    SPLIT = "SPLIT"


@dataclass(frozen=True, slots=True)
class PortfolioEvent:
    portfolio_id: int
    kind: PortfolioEventType
    occurred_at: datetime
    amount: Decimal = Decimal(0)
    withholding: Decimal = Decimal(0)
    asset: Asset | None = None
    ratio: Decimal | None = None
    currency: str = "BRL"
    note: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        validate_identity(self.portfolio_id, "portfolio_id")
        if self.id is not None:
            validate_identity(self.id, "id")
        if not isinstance(self.kind, PortfolioEventType) or not isinstance(
            self.occurred_at, datetime
        ):
            raise DomainValidationError("Tipo ou data do evento inválido.")
        if self.currency != "BRL":
            raise DomainValidationError(
                "Caixa suporta somente BRL; não há conversão cambial implícita."
            )
        validate_decimal(
            self.amount,
            "amount",
            positive=self.kind
            not in {PortfolioEventType.OPENING, PortfolioEventType.SPLIT},
        )
        validate_decimal(self.withholding, "withholding")
        if self.asset is not None and not isinstance(self.asset, Asset):
            raise DomainValidationError("Ativo inválido.")
        if self.kind == PortfolioEventType.SPLIT:
            if (
                self.asset is None
                or self.ratio is None
                or self.amount != 0
                or self.withholding != 0
            ):
                raise DomainValidationError(
                    "Desdobramento exige ativo e razão, sem valor de caixa."
                )
            validate_decimal(self.ratio, "ratio", positive=True)
        elif self.ratio is not None:
            raise DomainValidationError(
                "Razão é exclusiva de desdobramento/grupamento."
            )
        if self.kind in {PortfolioEventType.DIVIDEND, PortfolioEventType.JCP}:
            if self.asset is None or self.withholding > self.amount:
                raise DomainValidationError(
                    "Provento exige ativo e retenção não superior ao valor bruto."
                )
        elif self.withholding:
            raise DomainValidationError(
                "Retenção somente em proventos. Use evento de imposto para os demais."
            )

    @property
    def external_flow(self) -> Decimal:
        if self.kind == PortfolioEventType.DEPOSIT:
            return self.amount
        if self.kind == PortfolioEventType.WITHDRAWAL:
            return self.amount.copy_negate()
        return Decimal(0)

    @property
    def cash_effect(self) -> Decimal:
        if self.kind in {
            PortfolioEventType.WITHDRAWAL,
            PortfolioEventType.FEE,
            PortfolioEventType.TAX,
        }:
            return self.amount.copy_negate()
        span = (
            max(self.amount.adjusted(), self.withholding.adjusted())
            - min(
                int(self.amount.as_tuple().exponent),
                int(self.withholding.as_tuple().exponent),
            )
            + 1
        )
        with localcontext(Context(prec=max(50, span + 10))):
            return self.amount - self.withholding
