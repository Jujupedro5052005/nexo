from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset
from nexo.domain.models.position import Position


def position(**overrides) -> Position:
    fields = {
        "portfolio_id": 1,
        "asset": Asset("PETR4"),
        "quantity": Decimal(1),
        "average_cost": Decimal(30),
        "cost_basis": Decimal(30),
        "realized_profit_loss": Decimal(-2),
    }
    fields.update(overrides)
    return Position(**fields)


@pytest.mark.parametrize(
    "field, value",
    [
        ("portfolio_id", 0),
        ("asset", "PETR4"),
        ("quantity", Decimal(-1)),
        ("quantity", 1.0),
        ("average_cost", Decimal(0)),
        ("cost_basis", Decimal(0)),
        ("cost_basis", Decimal(-1)),
        ("average_cost", Decimal("NaN")),
        ("realized_profit_loss", 1.0),
        ("realized_profit_loss", Decimal("Infinity")),
    ],
)
def test_position_rejects_invalid_snapshot(field, value) -> None:
    with pytest.raises(DomainValidationError, match=field):
        position(**{field: value})


def test_position_closure_invariant_and_immutability() -> None:
    with pytest.raises(DomainValidationError, match="closed"):
        position(quantity=Decimal(0))
    closed = position(
        quantity=Decimal(0), average_cost=Decimal(0), cost_basis=Decimal(0)
    )
    assert closed.realized_profit_loss == Decimal(-2)
    with pytest.raises(FrozenInstanceError):
        closed.quantity = Decimal(1)
