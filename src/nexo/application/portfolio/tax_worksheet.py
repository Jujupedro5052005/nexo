"""Ledger reconciliation for a human tax review, not an official tax assessment."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.portfolio_event_repository import PortfolioEventRepository
from nexo.domain.reconstruction import rebuild_positions


@dataclass(frozen=True)
class TaxMonth:
    month: int
    sales: Decimal
    fees: Decimal
    realized: Decimal
    symbols: tuple[str, ...]


class BuildTaxWorksheet:
    def __init__(
        self,
        transactions: ListTransactions,
        events: PortfolioEventRepository | None = None,
    ) -> None:
        self.transactions, self.events = transactions, events

    def execute(self, portfolio_id: int, year: int) -> tuple[TaxMonth, ...]:
        with localcontext() as context:
            context.prec = 50
            return self._execute(portfolio_id, year)

    def _execute(self, portfolio_id: int, year: int) -> tuple[TaxMonth, ...]:
        if type(year) is not int or not 1900 <= year <= 2200:
            raise DomainValidationError("Ano inválido.")
        history = self.transactions.execute(portfolio_id)
        events = self.events.list_events(portfolio_id) if self.events else ()

        def realized(until: tuple[int, int]) -> Decimal:
            result = rebuild_positions(
                (
                    t
                    for t in history
                    if (t.occurred_at.year, t.occurred_at.month) <= until
                ),
                tuple(
                    e
                    for e in events
                    if (e.occurred_at.year, e.occurred_at.month) <= until
                ),
            )
            return sum(
                (
                    p.realized_profit_loss
                    for p in result.positions + result.closed_positions
                ),
                Decimal(0),
            )

        previous = realized((year - 1, 12))
        months = []
        for month in range(1, 13):
            subset = [
                t
                for t in history
                if (t.occurred_at.year, t.occurred_at.month) == (year, month)
            ]
            current = realized((year, month))
            months.append(
                TaxMonth(
                    month,
                    sum(
                        (
                            t.amounts()[0]
                            for t in subset
                            if t.transaction_type == TransactionType.SELL
                        ),
                        Decimal(0),
                    ),
                    sum((t.fees for t in subset), Decimal(0)),
                    current - previous,
                    tuple(sorted({t.asset.symbol for t in subset})),
                )
            )
            previous = current
        return tuple(months)
