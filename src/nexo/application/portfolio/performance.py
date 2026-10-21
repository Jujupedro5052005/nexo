from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from nexo.calculations.valuation.performance import (
    PortfolioPerformance,
    portfolio_performance,
)
from nexo.domain.interfaces.market_data_provider import (
    MarketDataError,
    MarketDataProvider,
)
from nexo.domain.interfaces.portfolio_event_repository import PortfolioEventRepository
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import PriceHistory


class LoadPortfolioPerformance:
    def __init__(
        self,
        transactions: TransactionRepository,
        events: PortfolioEventRepository,
        market: MarketDataProvider,
    ) -> None:
        self.transactions, self.events, self.market = transactions, events, market

    def execute(
        self, portfolio_id: int, *, end: date | None = None
    ) -> PortfolioPerformance:
        if self.events is self.transactions:
            trades, events = self.transactions.read_ledger(portfolio_id)
        else:
            trades = self.transactions.list_by_portfolio(portfolio_id)
            events = self.events.list_events(portfolio_id)
        end = end or (
            datetime.now(timezone.utc).astimezone().date() - timedelta(days=1)
        )
        if not events:
            return portfolio_performance(trades, events, {}, end)
        histories: dict[Asset, PriceHistory] = {}
        issues = []
        with self.market.refresh_context(True):
            for asset in dict.fromkeys(t.asset for t in trades):
                try:
                    quote = self.market.get_quote(asset)
                    if quote.currency != "BRL":
                        issues.append(
                            f"{asset.symbol}: moeda {quote.currency}, sem conversão BRL."
                        )
                        continue
                    histories[asset] = self.market.get_history(asset, "max")
                except MarketDataError as error:
                    issues.append(f"{asset.symbol}: {error}")
        result = portfolio_performance(trades, events, histories, end)
        if issues:
            return replace(result, twr=None, issues=tuple(issues) + result.issues)
        return result
