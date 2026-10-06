from nexo.application.portfolio.financial_summary import (
    FinancialSummary,
    summarize_portfolio,
)
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.reconstruction import ReconstructionResult, rebuild_positions


class LoadPortfolioPositions:
    def __init__(self, repository: TransactionRepository) -> None:
        self._list_transactions = ListTransactions(repository)

    def execute(self, portfolio_id: int) -> ReconstructionResult:
        return rebuild_positions(self._list_transactions.execute(portfolio_id))

    def summary(self, portfolio_id: int) -> FinancialSummary:
        history = self._list_transactions.execute(portfolio_id)
        return summarize_portfolio(history, rebuild_positions(history))
