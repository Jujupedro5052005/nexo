from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nexo.domain._validation import validate_decimal, validate_identity
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset


@dataclass(frozen=True, slots=True, eq=False)
class Transaction:
    """Immutable ledger entity; persistence is deliberately outside this increment."""

    portfolio_id: int
    asset: Asset
    transaction_type: TransactionType
    quantity: Decimal
    unit_price: Decimal
    fees: Decimal
    occurred_at: datetime
    id: int | None = None

    def __post_init__(self) -> None:
        validate_identity(self.portfolio_id, "portfolio_id")
        if self.id is not None:
            validate_identity(self.id, "id")
        if not isinstance(self.asset, Asset):
            raise DomainValidationError("asset must be Asset.")
        if not isinstance(self.transaction_type, TransactionType):
            raise DomainValidationError("transaction_type must be TransactionType.")
        if not isinstance(self.occurred_at, datetime):
            raise DomainValidationError("occurred_at must be datetime.")
        validate_decimal(self.quantity, "quantity", positive=True)
        validate_decimal(self.unit_price, "unit_price", positive=True)
        validate_decimal(self.fees, "fees")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        if self.id is None or other.id is None:
            return self is other
        return self.id == other.id

    def __hash__(self) -> int:
        return object.__hash__(self) if self.id is None else hash(self.id)
