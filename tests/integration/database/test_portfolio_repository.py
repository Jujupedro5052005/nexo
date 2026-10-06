from pathlib import Path

import pytest
from sqlalchemy import event, inspect
from sqlalchemy.exc import SQLAlchemyError

from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.infrastructure.database.models.portfolio_model import PortfolioModel
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    default_database_path,
    initialize_database,
)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "data" / "test.db"
    engine = create_database_engine(path)
    initialize_database(engine)
    try:
        yield path, engine
    finally:
        engine.dispose()


def test_schema_preserves_portfolios_with_id_and_name(database) -> None:
    path, engine = database
    assert path.is_file()
    inspector = inspect(engine)
    assert inspector.get_table_names() == ["portfolios", "transactions"]
    assert [column["name"] for column in inspector.get_columns("portfolios")] == ["id", "name"]
    assert inspector.get_pk_constraint("portfolios")["constrained_columns"] == ["id"]


def test_store_and_list_assigns_integer_identity_without_mutating_input(database) -> None:
    _, engine = database
    repository = SqlAlchemyPortfolioRepository(create_session_factory(engine))
    original = Portfolio(name="  Reserva de emergência  ")
    persisted = repository.add(original)
    assert type(persisted.id) is int
    assert original.id is None
    assert repository.list_all() == [persisted]
    assert repository.list_all()[0].name == "Reserva de emergência"


def test_duplicate_names_survive_new_engine_and_repository(database) -> None:
    path, engine = database
    repository = SqlAlchemyPortfolioRepository(create_session_factory(engine))
    first = repository.add(Portfolio(name="Longo Prazo"))
    second = repository.add(Portfolio(name="Longo Prazo"))
    assert first.id != second.id
    engine.dispose()
    reopened = create_database_engine(path)
    try:
        initialize_database(reopened)
        loaded = SqlAlchemyPortfolioRepository(create_session_factory(reopened)).list_all()
        assert [p.id for p in loaded] == [first.id, second.id]
        assert [p.name for p in loaded] == ["Longo Prazo", "Longo Prazo"]
    finally:
        reopened.dispose()


def test_failure_after_flush_rolls_back_and_allows_retry(database) -> None:
    _, engine = database
    factory = create_session_factory(engine)
    repository = SqlAlchemyPortfolioRepository(factory)

    def fail_commit(_session):
        raise SQLAlchemyError("Technical failure that must not reach UI")

    event.listen(factory, "before_commit", fail_commit)
    try:
        with pytest.raises(PortfolioRepositoryError, match="salvar"):
            repository.add(Portfolio(name="Não persistida"))
    finally:
        event.remove(factory, "before_commit", fail_commit)
    assert repository.list_all() == []
    assert repository.add(Portfolio(name="Após falha")).id is not None


def test_read_failure_is_translated_to_repository_error(database) -> None:
    _, engine = database
    PortfolioModel.__table__.drop(engine)
    repository = SqlAlchemyPortfolioRepository(create_session_factory(engine))
    with pytest.raises(PortfolioRepositoryError, match="carregar"):
        repository.list_all()


def test_already_persisted_entity_cannot_be_added_again(database) -> None:
    _, engine = database
    repository = SqlAlchemyPortfolioRepository(create_session_factory(engine))
    saved = repository.add(Portfolio(name="Carteira"))
    with pytest.raises(ValueError):
        repository.add(saved)
    assert repository.list_all() == [saved]


def test_default_path_is_independent_of_current_directory(tmp_path, monkeypatch) -> None:
    expected = Path(__file__).resolve().parents[3] / "data" / "nexo.db"
    monkeypatch.chdir(tmp_path)
    assert default_database_path() == expected
