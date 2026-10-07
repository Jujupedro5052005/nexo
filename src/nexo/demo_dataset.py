"""DEMO DATA — valores fictícios para apresentação, never market-price fixtures.

This bootstrap composes the existing use cases and repositories, just like main.
Only a file named nexo_demo.db may be replaced. No provider is instantiated.
"""

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    default_database_path,
    initialize_database,
)

DEMO_NOTICE = "DEMO DATA — valores fictícios para apresentação"

# Four manually chosen, illustrative entry prices per real B3 symbol. These are
# neither verified historical closes nor current quotes; no splits are simulated.
ENTRY_PRICES = {
    "ITUB4": ("32.40", "34.20", "31.80", "37.10"),
    "PETR4": ("38.60", "36.10", "32.80", "37.50"),
    "VALE3": ("63.20", "57.80", "54.60", "61.40"),
    "WEGE3": ("37.40", "45.80", "39.60", "42.20"),
    "BBAS3": ("28.40", "27.80", "24.60", "25.20"),
    "B3SA3": ("12.20", "10.40", "11.80", "13.60"),
    "IVVB11": ("298.00", "362.00", "348.00", "405.00"),
    "BOVA11": ("126.00", "122.00", "133.00", "145.00"),
    "TAEE11": ("35.80", "34.60", "33.20", "37.40"),
    "ITSA4": ("10.10", "10.60", "9.40", "11.20"),
    "BBSE3": ("33.80", "37.20", "34.10", "35.60"),
    "EGIE3": ("42.60", "40.80", "38.40", "43.20"),
    "RENT3": ("52.40", "48.80", "39.60", "45.20"),
    "TOTS3": ("28.60", "31.40", "34.80", "39.20"),
    "RADL3": ("27.40", "25.60", "20.80", "23.20"),
    "PRIO3": ("46.20", "43.60", "37.80", "41.40"),
}


@dataclass(frozen=True, slots=True)
class DemoPortfolioSpec:
    name: str
    lots: tuple[tuple[str, int], ...]
    partial_sales: tuple[str, ...]


DEMO_PORTFOLIOS = (
    DemoPortfolioSpec(
        "Longo Prazo",
        (("ITUB4", 100), ("PETR4", 100), ("VALE3", 60), ("WEGE3", 80),
         ("BBAS3", 120), ("B3SA3", 160), ("IVVB11", 15), ("BOVA11", 20)),
        ("PETR4", "VALE3", "B3SA3"),
    ),
    DemoPortfolioSpec(
        "Dividendos",
        (("BBAS3", 100), ("TAEE11", 80), ("ITSA4", 200), ("PETR4", 80),
         ("BBSE3", 80), ("EGIE3", 40), ("B3SA3", 60)),
        ("ITSA4", "BBSE3", "EGIE3"),
    ),
    DemoPortfolioSpec(
        "Crescimento",
        (("WEGE3", 40), ("RENT3", 40), ("TOTS3", 30), ("RADL3", 60),
         ("PRIO3", 60), ("IVVB11", 6)),
        ("WEGE3", "RENT3", "RADL3"),
    ),
)


@dataclass(frozen=True, slots=True)
class DemoPortfolioSummary:
    name: str
    portfolio_id: int
    assets: int
    transactions: int
    cost_basis: Decimal
    realized_profit_loss: Decimal


def demo_database_path() -> Path:
    return default_database_path().with_name("nexo_demo.db")


def _demo_target(path: Path | None) -> Path:
    candidate = path if path is not None else demo_database_path()
    if candidate.is_symlink() or candidate.name != "nexo_demo.db":
        raise ValueError("O seed só pode substituir um arquivo chamado nexo_demo.db.")
    target = candidate.resolve()
    normal = default_database_path().resolve()
    if target == normal or (
        target.exists() and normal.exists() and os.path.samefile(target, normal)
    ):
        raise ValueError("O banco normal não pode ser usado como banco demo.")
    return target


def _date(month_offset: int, day: int) -> datetime:
    # Naive wall-clock dates match TransactionDialog and the existing ledger.
    year, month = divmod(2024 * 12 + 3 + month_offset, 12)
    value = datetime(year, month + 1, day, 14, 30)  # noqa: DTZ001
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def _transactions(
    spec: DemoPortfolioSpec, portfolio_id: int, offset: int
) -> list[Transaction]:
    items = []
    for index, (symbol, lot) in enumerate(spec.lots):
        for round_number, price in enumerate(ENTRY_PRICES[symbol]):
            items.append(Transaction(
                portfolio_id, Asset(symbol), TransactionType.BUY,
                Decimal(lot), Decimal(price), Decimal("1.90") + Decimal(index) / 10,
                _date(round_number * 7 + index + offset, 8 + index),
            ))
        if symbol in spec.partial_sales:
            sale_index = spec.partial_sales.index(symbol)
            factor = (Decimal("1.12"), Decimal("0.87"), Decimal("1.08"))[sale_index]
            sale_price = (Decimal(ENTRY_PRICES[symbol][-1]) * factor).quantize(Decimal(".01"))
            items.append(Transaction(
                portfolio_id, Asset(symbol), TransactionType.SELL,
                Decimal(lot) * Decimal("0.4"), sale_price, Decimal("2.40"),
                _date(29, 18 + sale_index),
            ))
    return sorted(items, key=lambda item: item.occurred_at)


def create_demo_dataset(path: Path | None = None) -> tuple[DemoPortfolioSummary, ...]:
    """Build and validate a fresh ledger, then atomically replace only the demo DB.

    Existing demo data remains intact if validation fails. Close the demo app
    before resetting on Windows. The user's database and API budgets are untouched.
    """
    target = _demo_target(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix="nexo_demo_", suffix=".sqlite3", dir=target.parent)
    os.close(descriptor)
    temporary = Path(filename)
    try:
        engine = create_database_engine(temporary)
        try:
            initialize_database(engine)
            factory = create_session_factory(engine)
            portfolios = SqlAlchemyPortfolioRepository(factory)
            repository = SqlAlchemyTransactionRepository(factory)
            create, register = CreatePortfolio(portfolios), RegisterTransaction(repository)
            load = LoadPortfolioPositions(repository)
            summaries = []
            for offset, spec in enumerate(DEMO_PORTFOLIOS):
                portfolio = create.execute(spec.name)
                assert portfolio.id is not None
                items = _transactions(spec, portfolio.id, offset)
                for item in items:
                    register.execute(item)
                result = load.summary(portfolio.id)
                summaries.append(DemoPortfolioSummary(
                    spec.name, portfolio.id, result.positions_count, result.transactions_count,
                    result.cost_basis, result.realized_profit_loss,
                ))
        finally:
            engine.dispose()
        temporary.replace(target)
        return tuple(summaries)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_demo_dataset() -> Path:
    """Seed on first launch only; subsequent launches preserve presentation trades."""
    path = _demo_target(None)
    if not path.exists():
        create_demo_dataset(path)
    return path
