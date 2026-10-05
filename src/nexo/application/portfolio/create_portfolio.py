from nexo.domain.interfaces.portfolio_repository import PortfolioRepository
from nexo.domain.models.portfolio import Portfolio


class CreatePortfolio:
    def __init__(self, repository: PortfolioRepository) -> None:
        self._repository = repository

    def execute(self, name: str) -> Portfolio:
        return self._repository.add(Portfolio(name=name))
