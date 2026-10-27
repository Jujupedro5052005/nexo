from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.models.position import Position
from nexo.domain.models.transaction import Transaction


def trade_total(quantity: Decimal, price: Decimal) -> Decimal:
    """Gross trade amount, without rounding the ledger's monetary values."""
    with localcontext(financial_context([quantity, price])):
        return quantity * price


def quantity_for_total(total: Decimal, price: Decimal) -> Decimal:
    """Size a simulated trade to eight decimals without exceeding its budget."""
    if not total.is_finite() or not price.is_finite() or total <= 0 or price <= 0:
        raise ValueError("Valor total e preço devem ser positivos e finitos.")
    with localcontext(financial_context([total, price])):
        return (total / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


@dataclass(frozen=True)
class TradePreview:
    available: Decimal
    remaining: Decimal
    average_cost: Decimal | None
    realized: Decimal | None


def preview_trade(transaction: Transaction, position: Position | None) -> TradePreview:
    quantity = position.quantity if position else Decimal(0)
    cost = position.cost_basis if position else Decimal(0)
    with localcontext(
        financial_context(
            [
                quantity,
                cost,
                transaction.quantity,
                transaction.unit_price,
                transaction.fees,
            ]
        )
    ):
        if transaction.transaction_type is TransactionType.BUY:
            remaining = quantity + transaction.quantity
            average = (cost + transaction.amounts()[0] + transaction.fees) / remaining
            return TradePreview(quantity, remaining, average, None)
        remaining = quantity - transaction.quantity
        realized = (
            (
                transaction.amounts()[0]
                - transaction.fees
                - (position.average_cost if position else Decimal(0))
                * transaction.quantity
            )
            if remaining >= 0
            else None
        )
        return TradePreview(
            quantity,
            remaining,
            position.average_cost if position and remaining > 0 else None,
            realized,
        )
