from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

import pytest

from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction


def transaction(**overrides) -> Transaction:
    fields = {
        "portfolio_id": 1,
        "asset": Asset("PETR4"),
        "transaction_type": TransactionType.BUY,
        "quantity": Decimal("1.25"),
        "unit_price": Decimal("30.12345"),
        "fees": Decimal(0),
        "occurred_at": datetime.fromisoformat("2026-01-01T00:00:00"),
    }
    fields.update(overrides)
    return Transaction(**fields)


@pytest.mark.parametrize("kind", list(TransactionType))
def test_valid_transaction_preserves_decimal(kind: TransactionType) -> None:
    quantity = Decimal("1.250000000000000000000000001")
    item = transaction(transaction_type=kind, quantity=quantity)
    assert item.quantity is quantity
    assert item.unit_price == Decimal("30.12345")
    assert item.id is None


@pytest.mark.parametrize(
    "field, value",
    [
        ("quantity", Decimal(0)),
        ("quantity", Decimal(-1)),
        ("unit_price", Decimal(0)),
        ("unit_price", Decimal(-1)),
        ("fees", Decimal(-1)),
        ("portfolio_id", 0),
        ("portfolio_id", -1),
        ("portfolio_id", True),
        ("portfolio_id", "1"),
        ("id", 0),
        ("id", -1),
        ("id", True),
        ("id", "1"),
        ("asset", "PETR4"),
        ("transaction_type", "BUY"),
        ("occurred_at", "2026-01-01"),
    ],
)
def test_invalid_transaction_fields(field, value) -> None:
    with pytest.raises(DomainValidationError, match=field):
        transaction(**{field: value})


@pytest.mark.parametrize("field", ["quantity", "unit_price", "fees"])
@pytest.mark.parametrize(
    "value",
    [
        1.5,
        1,
        "1",
        True,
        None,
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_financial_fields_require_finite_decimal(field, value) -> None:
    with pytest.raises(DomainValidationError, match=field):
        transaction(**{field: value})


def test_transaction_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        transaction().quantity = Decimal(-1)


def test_transaction_entity_identity_matches_portfolio_convention() -> None:
    first = transaction()
    assert first != transaction()
    assert first in {first}
    persisted = transaction(id=1)
    assert persisted == transaction(id=1, unit_price=Decimal(50))
    assert hash(persisted) == hash(transaction(id=1))
    assert persisted != transaction(id=2)
    assert persisted != Asset("PETR4")


def test_transaction_type_has_only_buy_and_sell() -> None:
    assert {kind.value for kind in TransactionType} == {"BUY", "SELL"}
