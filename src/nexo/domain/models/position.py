from dataclasses import dataclass
from decimal import Decimal

from nexo.domain._validation import validate_decimal, validate_identity
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset


@dataclass(frozen=True, slots=True)
class Position:
    """Derived snapshot, never persisted; realized result survives closure."""

    portfolio_id: int
    asset: Asset
    quantity: Decimal
    average_cost: Decimal
    cost_basis: Decimal
    realized_profit_loss: Decimal

    def __post_init__(self) -> None:
        validate_identity(self.portfolio_id, "portfolio_id")
        if not isinstance(self.asset, Asset):
            raise DomainValidationError("asset must be Asset.")
        validate_decimal(self.quantity, "quantity")
        validate_decimal(self.average_cost, "average_cost", positive=self.quantity > 0)
        validate_decimal(self.cost_basis, "cost_basis", positive=self.quantity > 0)
        if (
            not isinstance(self.realized_profit_loss, Decimal)
            or not self.realized_profit_loss.is_finite()
        ):
            raise DomainValidationError("realized_profit_loss must be finite Decimal.")
        if self.quantity == 0 and (self.cost_basis != 0 or self.average_cost != 0):
            raise DomainValidationError(
                "A closed position must have zero cost and average."
            )
