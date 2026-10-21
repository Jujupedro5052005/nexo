from nexo.application.portfolio.financial_summary import (
    FinancialSummary,
    summarize_portfolio,
)
from nexo.domain._validation import validate_identity
from nexo.domain.interfaces.transaction_repository import TransactionRepository
from nexo.domain.reconstruction import ReconstructionResult, rebuild_positions


class LoadPortfolioPositions:
    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    def execute(self, portfolio_id: int) -> ReconstructionResult:
        validate_identity(portfolio_id, "portfolio_id")
        history, events = self._repository.read_ledger(portfolio_id)
        return rebuild_positions(history, events)

    def summary(self, portfolio_id: int) -> FinancialSummary:
        validate_identity(portfolio_id, "portfolio_id")
        history, events = self._repository.read_ledger(portfolio_id)
        return summarize_portfolio(history, rebuild_positions(history, events))
