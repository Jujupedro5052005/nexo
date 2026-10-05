import pytest

from nexo.domain.interfaces.portfolio_repository import PortfolioRepository
from nexo.domain.models.portfolio import Portfolio


class InMemoryPortfolioRepository(PortfolioRepository):
    """Test double; unit/UI tests never open the application's database."""

    def __init__(self) -> None:
        self.portfolios: list[Portfolio] = []

    def add(self, portfolio: Portfolio) -> Portfolio:
        if portfolio.id is not None:
            raise ValueError("Expected a new portfolio")
        persisted = Portfolio(name=portfolio.name, id=len(self.portfolios) + 1)
        self.portfolios.append(persisted)
        return persisted

    def list_all(self) -> list[Portfolio]:
        return list(self.portfolios)


@pytest.fixture
def portfolio_repository() -> InMemoryPortfolioRepository:
    return InMemoryPortfolioRepository()
