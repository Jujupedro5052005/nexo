from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.models.asset import Asset
from nexo.domain.models.position import Position
from nexo.domain.models.transaction import Transaction


@dataclass(frozen=True, slots=True)
class ReconstructionResult:
    """Open positions are primary; closed snapshots retain realized P/L separately."""

    positions: tuple[Position, ...]
    closed_positions: tuple[Position, ...]


def order_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    """Official order shared by ledger reads and reconstruction."""
    history = list(transactions)
    if any(not isinstance(item, Transaction) for item in history):
        raise DomainValidationError("history must contain Transaction objects.")
    awareness = {item.occurred_at.utcoffset() is not None for item in history}
    if len(awareness) > 1:
        raise DomainValidationError("Cannot mix naive and aware occurred_at values.")

    def order(item: Transaction) -> tuple[datetime, bool, int]:
        date = item.occurred_at
        if date.utcoffset() is not None:
            date = date.astimezone(timezone.utc)
        return date, item.id is None, item.id if item.id is not None else 0

    return sorted(history, key=order)


def rebuild_positions(transactions: Iterable[Transaction]) -> ReconstructionResult:
    """Replay chronologically, then by known ID, then stable input order.

    At equal timestamps known IDs precede missing IDs. Missing IDs and complete
    ties retain input order. Output is sorted by portfolio ID and asset symbol.
    All timestamps must be naive, or all aware (normalized to UTC).
    Arithmetic uses a fresh local Decimal context, at least 50 significant digits.
    """
    history = order_transactions(transactions)

    groups: dict[tuple[int, Asset], list[Transaction]] = {}
    for item in history:
        groups.setdefault((item.portfolio_id, item.asset), []).append(item)
    snapshots = [_rebuild_position(group) for group in groups.values()]
    snapshots.sort(key=lambda p: (p.portfolio_id, p.asset.symbol))
    return ReconstructionResult(
        positions=tuple(p for p in snapshots if p.quantity > 0),
        closed_positions=tuple(p for p in snapshots if p.quantity == 0),
    )


def _rebuild_position(history: list[Transaction]) -> Position:
    # Precision is scoped to one portfolio/asset, so unrelated transactions
    # cannot change even the representation of a recurring average cost.
    values = [
        value
        for item in history
        for value in (item.quantity, item.unit_price, item.fees)
    ]
    span = (
        max(value.adjusted() for value in values)
        - min(int(value.as_tuple().exponent) for value in values)
        + 1
    )
    precision = max(50, 2 * span + len(str(len(history))) + 10)
    zero = Decimal(0)
    previous = Position(
        history[0].portfolio_id, history[0].asset, zero, zero, zero, zero
    )
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_EVEN)):
        for item in history:
            realized = previous.realized_profit_loss
            if item.transaction_type is TransactionType.BUY:
                quantity = previous.quantity + item.quantity
                basis = previous.cost_basis + item.amounts()[1]
                average = basis / quantity
            else:
                if item.quantity > previous.quantity:
                    raise InsufficientPositionError(
                        item.portfolio_id,
                        item.asset.symbol,
                        previous.quantity,
                        item.quantity,
                    )
                quantity = previous.quantity - item.quantity
                # Consume the exact remaining basis on closure, including any
                # rounding remainder from a recurring average cost.
                removed = (
                    previous.cost_basis
                    if quantity == 0
                    else item.quantity * previous.average_cost
                )
                realized += item.amounts()[1] - removed
                basis = previous.cost_basis - removed if quantity else zero
                average = previous.average_cost if quantity else zero
            previous = Position(
                item.portfolio_id, item.asset, quantity, average, basis, realized
            )
    return previous
