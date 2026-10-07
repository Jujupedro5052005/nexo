from collections.abc import Iterable
from dataclasses import dataclass

from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class ComparedPortfolio:
    portfolio_id: int
    name: str
    transactions_count: int
    valuation: PortfolioValuation


class ComparePortfolios:
    def __init__(
        self,
        portfolios: ListPortfolios,
        transactions: ListTransactions,
        valuation: LoadPortfolioValuation,
    ) -> None:
        self._portfolios, self._transactions, self._valuation = (
            portfolios,
            transactions,
            valuation,
        )

    def execute(
        self, portfolio_ids: Iterable[int], *, refresh: bool = False
    ) -> tuple[ComparedPortfolio, ...]:
        identities = tuple(dict.fromkeys(portfolio_ids))
        if len(identities) < 2 or any(type(i) is not int or i <= 0 for i in identities):
            raise DomainValidationError(
                "Selecione pelo menos duas carteiras diferentes por ID."
            )
        available = {p.id: p for p in self._portfolios.execute()}
        if any(identity not in available for identity in identities):
            raise DomainValidationError(
                "Uma das carteiras selecionadas não está disponível."
            )
        if refresh:
            self._valuation.invalidate_cache()
        values = self._valuation.execute_many(identities, explicit=refresh)
        return tuple(
            ComparedPortfolio(
                identity,
                available[identity].name,
                len(self._transactions.execute(identity)),
                values[identity],
            )
            for identity in identities
        )
