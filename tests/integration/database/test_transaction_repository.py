from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.asset import Asset
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions
from nexo.infrastructure.database.models.portfolio_model import PortfolioModel
from nexo.infrastructure.database.models.transaction_model import TransactionModel
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)

START = datetime.fromisoformat("2026-01-01T10:00:00.123456")


def trade(
    portfolio=1,
    kind=TransactionType.BUY,
    quantity="10",
    price="30",
    fees="0",
    date=START,
):
    return Transaction(
        portfolio,
        Asset(" petr4 "),
        kind,
        Decimal(quantity),
        Decimal(price),
        Decimal(fees),
        date,
    )


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "ledger.db"
    engine = create_database_engine(path)
    initialize_database(engine)
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    portfolios.add(Portfolio("Igual"))
    portfolios.add(Portfolio("Igual"))
    try:
        yield path, engine, factory, SqlAlchemyTransactionRepository(factory)
    finally:
        engine.dispose()


@pytest.mark.parametrize("kind", list(TransactionType))
def test_persistence_assigns_id_and_roundtrips_enum_asset(ledger, kind) -> None:
    _, _, _, repository = ledger
    original = trade(kind=kind)
    saved = repository.add(original)
    assert original.id is None
    assert type(saved.id) is int and saved.id > 0
    loaded = repository.list_by_portfolio(1)[0]
    assert loaded.id == saved.id
    assert loaded.asset == Asset("PETR4")
    assert loaded.transaction_type is kind
    assert loaded.quantity == original.quantity


def test_foreign_keys_are_enabled_on_every_connection_and_reject_orphan(ledger) -> None:
    _, engine, _, repository = ledger
    for _ in range(2):
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        engine.dispose()
    with pytest.raises(TransactionRepositoryError):
        repository.add(trade(portfolio=999))
    assert repository.list_by_portfolio(999) == []
    assert repository.add(trade()).id is not None


@pytest.mark.parametrize(
    "value",
    [
        "0.1",
        "1.25",
        "0.3333333333333333333333333333",
        "123456789.123456789",
        "1.23456789012345678901234567890123456789",
    ],
)
def test_decimal_text_roundtrip_never_uses_float(ledger, value) -> None:
    _, engine, _, repository = ledger
    item = trade(quantity=value, price=value, fees=value)
    saved = repository.add(item)
    loaded = repository.list_by_portfolio(1)[0]
    assert (loaded.quantity, loaded.unit_price, loaded.fees) == (
        item.quantity,
        item.unit_price,
        item.fees,
    )
    assert loaded.quantity.as_tuple() == item.quantity.as_tuple()
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT typeof(quantity), quantity, unit_price, fees FROM transactions WHERE id=:id"
            ),
            {"id": saved.id},
        ).one()
    assert tuple(row) == ("text", value, value, value)


@pytest.mark.parametrize(
    "occurred_at",
    [
        START,
        START.replace(tzinfo=timezone.utc),
        START.replace(tzinfo=timezone(timedelta(hours=-3))),
        START.replace(tzinfo=timezone(timedelta(hours=5, minutes=30))),
    ],
)
def test_datetime_roundtrip_preserves_microseconds_and_offset(
    ledger, occurred_at
) -> None:
    _, _, _, repository = ledger
    repository.add(trade(date=occurred_at))
    loaded = repository.list_by_portfolio(1)[0]
    assert loaded.occurred_at == occurred_at
    assert loaded.occurred_at.isoformat() == occurred_at.isoformat()
    assert loaded.occurred_at.utcoffset() == occurred_at.utcoffset()


def test_order_and_portfolio_isolation(ledger) -> None:
    _, _, _, repository = ledger
    late = repository.add(trade(date=START + timedelta(hours=2)))
    other = repository.add(trade(portfolio=2))
    early = repository.add(trade())
    assert [t.id for t in repository.list_by_portfolio(1)] == [early.id, late.id]
    assert [t.id for t in repository.list_by_portfolio(2)] == [other.id]


def test_aware_order_uses_instants_instead_of_iso_text(ledger) -> None:
    _, _, _, repository = ledger
    late = repository.add(
        trade(date=START.replace(tzinfo=timezone(timedelta(hours=-3))))
    )
    early = repository.add(
        trade(
            date=(START + timedelta(hours=1)).replace(
                tzinfo=timezone(timedelta(hours=2))
            )
        )
    )
    assert [t.id for t in repository.list_by_portfolio(1)] == [early.id, late.id]


def test_failure_after_flush_rolls_back_and_recovers(ledger) -> None:
    _, _, factory, repository = ledger

    def fail(_session):
        raise SQLAlchemyError("Sensitive SQL details")

    event.listen(factory, "before_commit", fail)
    try:
        with pytest.raises(TransactionRepositoryError, match="salvar"):
            repository.add(trade())
    finally:
        event.remove(factory, "before_commit", fail)
    assert repository.list_by_portfolio(1) == []
    assert repository.add(trade()).id is not None


def test_read_failure_is_translated(ledger) -> None:
    _, engine, _, repository = ledger
    TransactionModel.__table__.drop(engine)
    with pytest.raises(TransactionRepositoryError, match="carregar"):
        repository.list_by_portfolio(1)


def test_persisted_entity_cannot_be_readded(ledger) -> None:
    _, _, _, repository = ledger
    saved = repository.add(trade())
    with pytest.raises(DomainValidationError):
        repository.add(saved)
    assert len(repository.list_by_portfolio(1)) == 1


def test_old_portfolio_only_database_is_upgraded_without_data_loss(tmp_path) -> None:
    engine = create_database_engine(tmp_path / "old.db")
    try:
        PortfolioModel.__table__.create(engine)
        portfolios = SqlAlchemyPortfolioRepository(create_session_factory(engine))
        saved = portfolios.add(Portfolio("Anterior"))
        initialize_database(engine)
        assert inspect(engine).get_table_names() == ["portfolios", "transactions"]
        assert portfolios.list_all()[0].id == saved.id
        assert portfolios.list_all()[0].name == "Anterior"
        columns = {c["name"] for c in inspect(engine).get_columns("transactions")}
        assert columns == {
            "id",
            "portfolio_id",
            "asset_symbol",
            "transaction_type",
            "quantity",
            "unit_price",
            "fees",
            "occurred_at",
        }
        assert (
            inspect(engine).get_foreign_keys("transactions")[0]["referred_table"]
            == "portfolios"
        )
    finally:
        engine.dispose()


def test_representative_history_reopens_and_invalid_sale_does_not_persist(
    ledger,
) -> None:
    path, engine, _, repository = ledger
    register = RegisterTransaction(repository)
    register.execute(trade(fees="2"))
    register.execute(trade(price="40", fees="2", date=START + timedelta(hours=1)))
    register.execute(
        trade(
            kind=TransactionType.SELL,
            quantity="5",
            price="42",
            fees="1",
            date=START + timedelta(hours=2),
        )
    )
    expected = rebuild_positions(repository.list_by_portfolio(1))
    engine.dispose()
    reopened = create_database_engine(path)
    try:
        initialize_database(reopened)
        repository = SqlAlchemyTransactionRepository(create_session_factory(reopened))
        result = rebuild_positions(repository.list_by_portfolio(1))
        assert result == expected
        p = result.positions[0]
        assert (
            p.quantity,
            p.average_cost,
            p.cost_basis,
            p.realized_profit_loss,
        ) == tuple(map(Decimal, ("15", "35.2", "528", "33")))
        with pytest.raises(InsufficientPositionError):
            RegisterTransaction(repository).execute(
                trade(
                    kind=TransactionType.SELL,
                    quantity="16",
                    price="50",
                    date=START + timedelta(hours=3),
                )
            )
        assert len(repository.list_by_portfolio(1)) == 3
    finally:
        reopened.dispose()


def test_same_timestamp_validation_equals_committed_reconstruction(ledger) -> None:
    _, _, _, repository = ledger
    register = RegisterTransaction(repository)
    buy = register.execute(trade())
    sell = trade(kind=TransactionType.SELL, quantity="5", price="42")
    before = rebuild_positions([buy, sell])
    saved = register.execute(sell)
    assert saved.id > buy.id
    assert rebuild_positions(repository.list_by_portfolio(1)) == before
    with pytest.raises(InsufficientPositionError):
        register.execute(replace(sell, quantity=Decimal(6)))
    assert len(repository.list_by_portfolio(1)) == 2
