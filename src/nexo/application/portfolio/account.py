from dataclasses import dataclass, replace
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.calculations.valuation.portfolio import PortfolioValuation, value_portfolio
from nexo.domain.interfaces.market_data_provider import MarketDataProvider
from nexo.domain.interfaces.portfolio_event_repository import PortfolioEventRepository
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.models.portfolio_event import PortfolioEvent
from nexo.domain.reconstruction import rebuild_positions
from nexo.domain.services.cash_ledger import CashState, cash_state


@dataclass(frozen=True)
class AccountSnapshot:
    cash: CashState
    events: tuple[PortfolioEvent, ...]
    market_value: Decimal | None
    equity: Decimal | None


class PortfolioAccount:
    def __init__(
        self,
        transactions: TransactionRepository,
        events: PortfolioEventRepository,
        market: MarketDataProvider,
    ) -> None:
        self.transactions, self.events, self.market = transactions, events, market

    def register(self, event: PortfolioEvent) -> PortfolioEvent:
        return self.events.add_event(event)

    def load(self, portfolio_id: int, *, quoted: bool = False) -> AccountSnapshot:
        if self.events is self.transactions:
            trades, events = self.transactions.read_ledger(portfolio_id)
        else:
            trades = self.transactions.list_by_portfolio(portfolio_id)
            events = self.events.list_events(portfolio_id)
        cash = cash_state(trades, events)
        market_value = None
        if quoted:
            positions = rebuild_positions(trades, events)
            with self.market.refresh_context(True):
                quotes = self.market.get_quotes(p.asset for p in positions.positions)
            market_value = value_portfolio(positions, quotes).current_market_value
        equity = (
            cash.balance + market_value
            if cash.balance is not None and market_value is not None
            else None
        )
        return AccountSnapshot(cash, events, market_value, equity)

    def valued(
        self, portfolio_id: int, valuation: PortfolioValuation
    ) -> AccountSnapshot:
        snapshot = self.load(portfolio_id)
        value, cash = valuation.current_market_value, snapshot.cash.balance
        with localcontext(
            financial_context([v for v in (value, cash) if v is not None])
        ):
            return replace(
                snapshot,
                market_value=value,
                equity=cash + value if cash is not None and value is not None else None,
            )
