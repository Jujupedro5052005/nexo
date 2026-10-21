from abc import ABC, abstractmethod

from nexo.domain.models.portfolio_event import PortfolioEvent
from nexo.domain.models.transaction import Transaction


class TransactionRepositoryError(Exception):
    """Storage failure translated without leaking infrastructure details."""


class TransactionRepository(ABC):
    """Append-only ledger; generated IDs must exceed all existing ledger IDs."""

    @abstractmethod
    def add(self, transaction: Transaction) -> Transaction:
        """Commit a new transaction and return its generated identity."""

    @abstractmethod
    def list_by_portfolio(self, portfolio_id: int) -> list[Transaction]:
        """Return domain entities in the official chronological order."""

    def list_events(self, portfolio_id: int) -> tuple["PortfolioEvent", ...]:
        return ()

    def read_ledger(
        self, portfolio_id: int
    ) -> tuple[list[Transaction], tuple[PortfolioEvent, ...]]:
        """Storage implementations can provide one coherent read snapshot."""
        return self.list_by_portfolio(portfolio_id), self.list_events(portfolio_id)

    def add_validated(self, transaction: Transaction) -> Transaction:
        from nexo.domain.reconstruction import rebuild_positions
        from nexo.domain.services.cash_ledger import cash_state

        history = self.list_by_portfolio(transaction.portfolio_id)
        events = self.list_events(transaction.portfolio_id)
        rebuild_positions([*history, transaction], events)
        cash_state([*history, transaction], events)
        return self.add(transaction)
