from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import order_transactions, rebuild_positions


@dataclass(frozen=True)
class LedgerPoint:
    month: str
    cost: Decimal
    realized: Decimal


def ledger_timeline(transactions: list[Transaction]) -> tuple[LedgerPoint, ...]:
    """Month-end ledger snapshots; never substitute for historical market value."""
    ordered = order_transactions(transactions)
    points = []
    for index, transaction in enumerate(ordered):
        month = transaction.occurred_at.strftime("%Y-%m")
        if (
            index + 1 < len(ordered)
            and ordered[index + 1].occurred_at.strftime("%Y-%m") == month
        ):
            continue
        result = rebuild_positions(ordered[: index + 1])
        with localcontext(
            financial_context(
                [
                    value
                    for p in result.positions + result.closed_positions
                    for value in (p.cost_basis, p.realized_profit_loss)
                ],
                count=len(result.positions + result.closed_positions),
            )
        ):
            cost = sum((p.cost_basis for p in result.positions), Decimal(0))
            realized = sum(
                (
                    p.realized_profit_loss
                    for p in result.positions + result.closed_positions
                ),
                Decimal(0),
            )
        points.append(LedgerPoint(month, cost, realized))
    return tuple(points)
