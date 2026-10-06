from abc import ABC, abstractmethod

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
