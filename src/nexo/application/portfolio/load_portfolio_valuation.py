from collections.abc import Iterable

from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.calculations.valuation.portfolio import PortfolioValuation, value_portfolio
from nexo.domain.interfaces.market_data_provider import (
    MarketDataError,
    MarketDataProvider,
    QuoteBatch,
    QuoteIssue,
)


class LoadPortfolioValuation:
    def __init__(
        self, load_positions: LoadPortfolioPositions, provider: MarketDataProvider
    ) -> None:
        self._load_positions = load_positions
        self._provider = provider

    def invalidate_cache(self) -> None:
        self._provider.invalidate()

    def execute(self, portfolio_id: int) -> PortfolioValuation:
        return self.execute_many([portfolio_id])[portfolio_id]

    def execute_many(
        self, portfolio_ids: Iterable[int], *, explicit: bool = False
    ) -> dict[int, PortfolioValuation]:
        with self._provider.refresh_context(explicit):
            return self._execute_many(portfolio_ids)

    def _execute_many(
        self, portfolio_ids: Iterable[int]
    ) -> dict[int, PortfolioValuation]:
        ledgers = {
            identity: self._load_positions.execute(identity)
            for identity in dict.fromkeys(portfolio_ids)
        }
        assets = {p.asset for result in ledgers.values() for p in result.positions}
        try:
            batch = (
                self._provider.get_quotes(
                    sorted(assets, key=lambda asset: asset.symbol)
                )
                if assets
                else QuoteBatch(())
            )
        except MarketDataError as error:
            batch = QuoteBatch(
                (),
                tuple(
                    QuoteIssue(asset, error)
                    for asset in sorted(assets, key=lambda asset: asset.symbol)
                ),
            )
        return {
            identity: value_portfolio(result, batch)
            for identity, result in ledgers.items()
        }
