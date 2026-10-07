from dataclasses import asdict
from datetime import datetime
from decimal import Decimal

import pytest

from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.demo_dataset import (
    DEMO_PORTFOLIOS,
    create_demo_dataset,
    ensure_demo_dataset,
)
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import InsufficientPositionError
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


@pytest.fixture
def demo_database(tmp_path):
    path = tmp_path / "nexo_demo.db"
    summaries = create_demo_dataset(path)
    engine = create_database_engine(path)
    factory = create_session_factory(engine)
    try:
        yield path, summaries, factory
    finally:
        engine.dispose()


def ledger_snapshot(path):
    engine = create_database_engine(path)
    try:
        factory = create_session_factory(engine)
        portfolios = ListPortfolios(SqlAlchemyPortfolioRepository(factory)).execute()
        repository = SqlAlchemyTransactionRepository(factory)
        return [(p.name, p.id, [asdict(t) for t in repository.list_by_portfolio(p.id)])
                for p in portfolios]
    finally:
        engine.dispose()


def test_three_portfolios_counts_and_reconstruction(demo_database):
    path, summaries, factory = demo_database
    assert path.exists()
    assert [(s.name, s.assets, s.transactions) for s in summaries] == [
        ("Longo Prazo", 8, 35), ("Dividendos", 7, 31), ("Crescimento", 6, 27)
    ]
    assert [s.portfolio_id for s in summaries] == [1, 2, 3]
    repository = SqlAlchemyTransactionRepository(factory)
    seen_ids = set()
    for summary, spec in zip(summaries, DEMO_PORTFOLIOS, strict=True):
        history = repository.list_by_portfolio(summary.portfolio_id)
        positions = LoadPortfolioPositions(repository).execute(summary.portfolio_id)
        assert len(history) == summary.transactions
        assert len(positions.positions) == summary.assets
        assert not positions.closed_positions
        assert {p.asset.symbol for p in positions.positions} == {s for s, _ in spec.lots}
        assert all(t.portfolio_id == summary.portfolio_id for t in history)
        for transaction in history:
            assert transaction.id is not None and transaction.id not in seen_ids
            seen_ids.add(transaction.id)
            assert all(v.is_finite() and v > 0 for v in (
                transaction.quantity, transaction.unit_price, transaction.fees
            ))
        assert all(p.quantity > 0 and p.average_cost > 0 and p.cost_basis > 0
                   for p in positions.positions)
    assert len(seen_ids) == 93


def test_thirty_months_recurring_buys_and_partial_sales(demo_database):
    _, summaries, factory = demo_database
    repository = SqlAlchemyTransactionRepository(factory)
    dates = set()
    realized = []
    for summary in summaries:
        history = repository.list_by_portfolio(summary.portfolio_id)
        balances = {}
        for transaction in history:
            dates.add((transaction.occurred_at.year, transaction.occurred_at.month))
            symbol = transaction.asset.symbol
            before = balances.get(symbol, Decimal(0))
            if transaction.transaction_type is TransactionType.SELL:
                assert 0 < transaction.quantity < before
                balances[symbol] = before - transaction.quantity
            else:
                balances[symbol] = before + transaction.quantity
        for symbol in balances:
            buys = [t for t in history if t.asset.symbol == symbol
                    and t.transaction_type is TransactionType.BUY]
            assert len(buys) == 4
            assert len({t.unit_price for t in buys}) == 4
        assert sum(t.transaction_type is TransactionType.SELL for t in history) == 3
        realized.extend(p.realized_profit_loss for p in rebuild_positions(history).positions)
    assert len(dates) == 30
    assert min(dates) == (2024, 4) and max(dates) == (2026, 9)
    assert any(value > 0 for value in realized) and any(value < 0 for value in realized)


def test_oversell_is_rejected_without_writing(demo_database):
    _, summaries, factory = demo_database
    repository = SqlAlchemyTransactionRepository(factory)
    identity = summaries[0].portfolio_id
    position = LoadPortfolioPositions(repository).execute(identity).positions[0]
    transaction = Transaction(
        identity, position.asset, TransactionType.SELL, position.quantity + 1,
        Decimal(30), Decimal(1), datetime(2026, 10, 7),  # noqa: DTZ001
    )
    before = repository.list_by_portfolio(identity)
    with pytest.raises(InsufficientPositionError):
        RegisterTransaction(repository).execute(transaction)
    assert repository.list_by_portfolio(identity) == before


def test_reset_is_idempotent_and_normal_database_untouched(tmp_path, monkeypatch):
    import nexo.demo_dataset as demo

    normal = tmp_path / "nexo.db"
    normal.write_bytes(b"user database must survive")
    monkeypatch.setattr(demo, "default_database_path", lambda: normal)
    path = tmp_path / "nexo_demo.db"
    first = create_demo_dataset(path)
    original = ledger_snapshot(path)
    assert create_demo_dataset(path) == first
    assert ledger_snapshot(path) == original
    assert normal.read_bytes() == b"user database must survive"
    with pytest.raises(ValueError):
        create_demo_dataset(normal)
    assert normal.read_bytes() == b"user database must survive"


def test_first_launch_creates_demo_and_relaunch_preserves_trades(tmp_path, monkeypatch):
    import nexo.demo_dataset as demo

    normal = tmp_path / "nexo.db"
    monkeypatch.setattr(demo, "default_database_path", lambda: normal)
    path = ensure_demo_dataset()
    engine = create_database_engine(path)
    try:
        repository = SqlAlchemyTransactionRepository(create_session_factory(engine))
        RegisterTransaction(repository).execute(Transaction(
            1, demo.Asset("PETR4"), TransactionType.BUY, Decimal(1), Decimal(30),
            Decimal(0), datetime(2026, 10, 7),  # noqa: DTZ001
        ))
    finally:
        engine.dispose()
    before = ledger_snapshot(path)
    assert ensure_demo_dataset() == path
    assert ledger_snapshot(path) == before
    assert len(before[0][2]) == 36
    assert not normal.exists()


def test_failed_build_keeps_existing_demo_and_removes_temporary_file(demo_database, monkeypatch):
    path, _, _ = demo_database
    before = path.read_bytes()

    def fail(*args):
        raise RuntimeError("seed validation failed")

    monkeypatch.setattr(RegisterTransaction, "execute", fail)
    with pytest.raises(RuntimeError, match="seed validation"):
        create_demo_dataset(path)
    assert path.read_bytes() == before
    assert not list(path.parent.glob("nexo_demo_*.sqlite3"))


def test_normal_database_hardlink_is_rejected(tmp_path, monkeypatch):
    import nexo.demo_dataset as demo

    normal = tmp_path / "nexo.db"
    normal.write_bytes(b"do not modify")
    path = tmp_path / "nexo_demo.db"
    try:
        path.hardlink_to(normal)
    except OSError:
        pytest.skip("Filesystem does not support hardlinks")
    monkeypatch.setattr(demo, "default_database_path", lambda: normal)
    with pytest.raises(ValueError):
        create_demo_dataset(path)
    assert normal.read_bytes() == b"do not modify"


@pytest.mark.parametrize("filename", ["nexo.db", "other.db"])
def test_refuses_other_targets(tmp_path, filename):
    with pytest.raises(ValueError):
        create_demo_dataset(tmp_path / filename)


@pytest.mark.parametrize("argv, demo", [([], False), (["--demo"], True)])
def test_cli_selects_mode_without_changing_normal_default(monkeypatch, argv, demo):
    import nexo.main as entry

    calls = []
    monkeypatch.setattr(entry, "main", lambda **kwargs: calls.append(kwargs) or 0)
    assert entry.cli(argv) == 0
    assert calls == [{"demo": demo}]
