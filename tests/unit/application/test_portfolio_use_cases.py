import pytest

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError


def test_create_returns_persisted_entity_with_normalized_name(portfolio_repository) -> None:
    result = CreatePortfolio(portfolio_repository).execute("  Minha carteira  ")
    assert result.name == "Minha carteira"
    assert result.id == 1
    assert portfolio_repository.portfolios == [result]


def test_invalid_name_does_not_reach_repository(portfolio_repository) -> None:
    with pytest.raises(ValueError):
        CreatePortfolio(portfolio_repository).execute("   ")
    assert portfolio_repository.portfolios == []


def test_create_allows_duplicate_names_with_distinct_identities(portfolio_repository) -> None:
    create = CreatePortfolio(portfolio_repository)
    first = create.execute("Longo Prazo")
    second = create.execute("Longo Prazo")
    assert first.name == second.name
    assert first.id != second.id


def test_list_returns_empty_result_without_portfolios(portfolio_repository) -> None:
    assert ListPortfolios(portfolio_repository).execute() == []


def test_list_returns_domain_entities(portfolio_repository) -> None:
    created = CreatePortfolio(portfolio_repository).execute("Carteira")
    assert ListPortfolios(portfolio_repository).execute() == [created]


def test_storage_failure_is_propagated_without_a_fake_result(
    portfolio_repository, monkeypatch,
) -> None:
    def fail(_portfolio):
        raise PortfolioRepositoryError("Falha de teste")

    monkeypatch.setattr(portfolio_repository, "add", fail)
    with pytest.raises(PortfolioRepositoryError):
        CreatePortfolio(portfolio_repository).execute("Carteira")
    assert portfolio_repository.portfolios == []
