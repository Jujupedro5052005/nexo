from dataclasses import dataclass
from decimal import Context, Decimal, localcontext

from nexo.calculations.risk.concentration import Concentration, concentration
from nexo.domain.interfaces.market_data_provider import QuoteBatch
from nexo.domain.models.market_data import Quote
from nexo.domain.models.position import Position
from nexo.domain.reconstruction import ReconstructionResult


@dataclass(frozen=True, slots=True)
class ValuedPosition:
    position: Position
    quote: Quote | None
    market_value: Decimal | None
    unrealized_profit_loss: Decimal | None
    unrealized_return: Decimal | None
    unavailable_reason: str = ""


@dataclass(frozen=True, slots=True)
class PortfolioValuation:
    positions: tuple[ValuedPosition, ...]
    invested_cost: Decimal
    current_market_value: Decimal | None
    realized_profit_loss: Decimal
    unrealized_profit_loss: Decimal | None
    total_profit_loss: Decimal | None
    unrealized_return: Decimal | None

    @property
    def concentration(self) -> Concentration:
        return concentration(self)

    @property
    def complete(self) -> bool:
        return self.current_market_value is not None


def value_portfolio(
    result: ReconstructionResult, batch: QuoteBatch
) -> PortfolioValuation:
    """Ledger cost is BRL. Never aggregate missing quotes or mixed currencies.

    Foreign-currency positions can display their own market value; their BRL P/L
    and the aggregate are unavailable. Percentages describe only open cost:
    unrealized P/L / remaining cost basis. No cash or total-return percentage.
    """
    quotes = {quote.asset: quote for quote in batch.quotes}
    issues = {issue.asset: str(issue.error) for issue in batch.issues}
    numbers = [
        n
        for p in result.positions + result.closed_positions
        for n in (p.quantity, p.cost_basis, p.realized_profit_loss)
    ]
    numbers += [q.price for q in batch.quotes]
    span = (
        max((n.adjusted() for n in numbers), default=0)
        - min((int(n.as_tuple().exponent) for n in numbers), default=0)
        + 1
    )
    valued: list[ValuedPosition] = []
    with localcontext(Context(prec=max(50, 2 * span + len(str(len(numbers))) + 10))):
        cost = sum((p.cost_basis for p in result.positions), Decimal(0))
        realized = sum(
            (
                p.realized_profit_loss
                for p in result.positions + result.closed_positions
            ),
            Decimal(0),
        )
        for p in result.positions:
            quote = quotes.get(p.asset)
            if quote is None:
                valued.append(
                    ValuedPosition(
                        p, None, None, None, None, issues.get(p.asset, "Sem cotação.")
                    )
                )
            else:
                market_value = p.quantity * quote.price
                if quote.currency != "BRL":
                    valued.append(
                        ValuedPosition(
                            p,
                            quote,
                            market_value,
                            None,
                            None,
                            f"Moeda {quote.currency}: custo do ledger em BRL, sem conversão cambial.",
                        )
                    )
                else:
                    unrealized = market_value - p.cost_basis
                    valued.append(
                        ValuedPosition(
                            p,
                            quote,
                            market_value,
                            unrealized,
                            unrealized / p.cost_basis if p.cost_basis > 0 else None,
                        )
                    )
        complete = all(p.unrealized_profit_loss is not None for p in valued)
        market = (
            sum(
                (p.market_value for p in valued if p.market_value is not None),
                Decimal(0),
            )
            if complete
            else None
        )
        unrealized_total = market - cost if market is not None else None
        total = realized + unrealized_total if unrealized_total is not None else None
        return PortfolioValuation(
            tuple(valued),
            cost,
            market,
            realized,
            unrealized_total,
            total,
            unrealized_total / cost
            if unrealized_total is not None and cost > 0
            else None,
        )
