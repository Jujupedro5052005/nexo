from nexo.domain.interfaces.portfolio_repository import PortfolioRepository
from nexo.domain.models.portfolio import Portfolio


class ListPortfolios:
    def __init__(self, repository: PortfolioRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Portfolio]:
        return self._repository.list_all()
