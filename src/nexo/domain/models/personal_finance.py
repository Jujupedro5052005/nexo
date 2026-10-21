from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from nexo.domain._validation import validate_decimal, validate_identity
from nexo.domain.errors import DomainValidationError


def valid_name(name: str) -> None:
    if not name.strip():
        raise DomainValidationError("Informe uma descrição.")


@dataclass(frozen=True)
class BudgetEntry:
    name: str
    amount: Decimal
    kind: str
    month: date
    id: int | None = None

    def __post_init__(self) -> None:
        if self.id is not None:
            validate_identity(self.id, "id")
        valid_name(self.name)
        validate_decimal(self.amount, "amount", positive=True)
        if self.kind not in {"income", "fixed", "variable"}:
            raise DomainValidationError("Tipo de lançamento inválido.")
        if type(self.month) is not date:
            raise DomainValidationError("Data inválida.")


@dataclass(frozen=True)
class FinancialGoal:
    name: str
    target: Decimal
    current: Decimal
    deadline: date
    id: int | None = None

    def __post_init__(self) -> None:
        if self.id is not None:
            validate_identity(self.id, "id")
        valid_name(self.name)
        validate_decimal(self.target, "target", positive=True)
        validate_decimal(self.current, "current")
        if type(self.deadline) is not date:
            raise DomainValidationError("Prazo inválido.")


@dataclass(frozen=True)
class PriceAlert:
    symbol: str
    threshold: Decimal
    direction: str
    enabled: bool = True
    checked_at: str = ""
    quote_at: str = ""
    state: str = "Não verificado"
    triggered_at: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        if self.id is not None:
            validate_identity(self.id, "id")
        if type(self.enabled) is not bool:
            raise DomainValidationError("Estado do alerta inválido.")
        from nexo.domain.models.asset import Asset

        object.__setattr__(self, "symbol", Asset(self.symbol).symbol)
        validate_decimal(self.threshold, "threshold", positive=True)
        if self.direction not in {"below", "above"}:
            raise DomainValidationError("Condição inválida.")
