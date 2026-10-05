from abc import ABC, abstractmethod

from nexo.domain.models.portfolio import Portfolio


class PortfolioRepositoryError(Exception):
    """A storage failure without exposing infrastructure types to callers."""


class PortfolioRepository(ABC):
    """Persistence operations required by the first portfolio use cases."""

    @abstractmethod
    def add(self, portfolio: Portfolio) -> Portfolio:
        """Store a new portfolio and return it with its generated identity."""

    @abstractmethod
    def list_all(self) -> list[Portfolio]:
        """Return persisted portfolios ordered by identity."""
