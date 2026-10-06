from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext

from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import ReconstructionResult


@dataclass(frozen=True, slots=True)
class FinancialSummary:
    positions_count: int
    transactions_count: int
    cost_basis: Decimal
    realized_profit_loss: Decimal


def _sum(values: Iterable[Decimal]) -> Decimal:
    numbers = list(values)
    span = (
        max((n.adjusted() for n in numbers), default=0)
        - min((int(n.as_tuple().exponent) for n in numbers), default=0)
        + 1
    )
    with localcontext(Context(prec=max(50, span + len(str(len(numbers))) + 2))):
        return sum(numbers, Decimal(0))


def summarize_portfolio(
    transactions: Iterable[Transaction], result: ReconstructionResult
) -> FinancialSummary:
    return FinancialSummary(
        positions_count=len(result.positions),
        transactions_count=len(list(transactions)),
        cost_basis=_sum(p.cost_basis for p in result.positions),
        realized_profit_loss=_sum(
            p.realized_profit_loss for p in result.positions + result.closed_positions
        ),
    )


def transaction_amounts(transaction: Transaction) -> tuple[Decimal, Decimal]:
    """Gross and settlement amounts; UI only formats these application results."""
    return transaction.amounts()
