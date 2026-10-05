from dataclasses import FrozenInstanceError

import pytest

from nexo.domain.models.portfolio import Portfolio


def test_new_portfolio_has_valid_name_and_no_persisted_identity() -> None:
    portfolio = Portfolio(name="Longo Prazo")
    assert portfolio.name == "Longo Prazo"
    assert portfolio.id is None


def test_name_is_trimmed_without_changing_internal_spaces() -> None:
    assert Portfolio(name="  Minha  carteira \t").name == "Minha  carteira"


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_blank_name_is_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="nome"):
        Portfolio(name=name)


def test_same_name_does_not_make_new_portfolios_the_same_entity() -> None:
    first = Portfolio(name="Longo Prazo")
    second = Portfolio(name="Longo Prazo")
    assert first != second


def test_persisted_identity_is_independent_of_name() -> None:
    first = Portfolio(id=1, name="Longo Prazo")
    same_identity = Portfolio(id=1, name="Outro nome")
    other_identity = Portfolio(id=2, name="Longo Prazo")
    assert first == same_identity
    assert hash(first) == hash(same_identity)
    assert first != other_identity


@pytest.mark.parametrize("identity", [0, -1, True])
def test_invalid_identity_is_rejected(identity: int) -> None:
    with pytest.raises(ValueError, match="identificador"):
        Portfolio(id=identity, name="Carteira")


def test_structural_data_cannot_be_changed_bypassing_validation() -> None:
    portfolio = Portfolio(name="Carteira")
    with pytest.raises(FrozenInstanceError):
        portfolio.name = ""
    with pytest.raises(FrozenInstanceError):
        portfolio.id = 42
