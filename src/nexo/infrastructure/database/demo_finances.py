"""Idempotent sample data, restricted to the separate demonstration database."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Engine, insert, select, text, update

from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.domain.services.cash_ledger import cash_state
from nexo.infrastructure.database.models.personal_finance import (
    AlertModel,
    BudgetModel,
    GoalModel,
)
from nexo.infrastructure.database.models.portfolio_event import PortfolioEventModel
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import create_session_factory


def seed_demo_finances(engine: Engine) -> None:
    path = Path(str(engine.url.database))
    if (
        path.name != "nexo_demo.db"
        or path.is_symlink()
        or path.resolve().name != "nexo_demo.db"
    ):
        raise ValueError("Exemplos só podem ser gravados no banco demo.")
    _seed_accounts(engine)
    today = datetime.now().astimezone().date()
    with engine.begin() as connection:
        for model, names in (
            (
                BudgetModel,
                (
                    "Renda mensal",
                    "Moradia e contas",
                    "Alimentação e transporte",
                    "Lazer e imprevistos",
                ),
            ),
            (
                GoalModel,
                ("Reserva de emergência", "Aporte de longo prazo", "Viagem planejada"),
            ),
        ):
            for name in names:
                connection.execute(
                    update(model)
                    .where(model.name == f"DEMO · {name}")
                    .values(name=name)
                )
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS demo_seed_versions (name TEXT PRIMARY KEY)"
            )
        )
        if connection.execute(
            text("SELECT name FROM demo_seed_versions WHERE name='finances_v1'")
        ).first():
            return
        # Preserve any records already entered in an existing demo environment.
        if not connection.execute(select(BudgetModel.id).limit(1)).first():
            connection.execute(
                insert(BudgetModel),
                [
                    {
                        "name": name,
                        "amount": amount,
                        "kind": kind,
                        "month": today.replace(day=1).isoformat(),
                    }
                    for name, amount, kind in (
                        ("Renda mensal", "8500", "income"),
                        ("Moradia e contas", "2800", "fixed"),
                        ("Alimentação e transporte", "1700", "variable"),
                        ("Lazer e imprevistos", "700", "variable"),
                    )
                ],
            )
        if not connection.execute(select(GoalModel.id).limit(1)).first():
            connection.execute(
                insert(GoalModel),
                [
                    {
                        "name": name,
                        "target": target,
                        "current": current,
                        "deadline": (today + timedelta(days=days)).isoformat(),
                    }
                    for name, target, current, days in (
                        ("Reserva de emergência", "30000", "18000", 365),
                        ("Aporte de longo prazo", "100000", "42000", 1095),
                        ("Viagem planejada", "18000", "6500", 540),
                    )
                ],
            )
        if not connection.execute(select(AlertModel.id).limit(1)).first():
            connection.execute(
                insert(AlertModel),
                [
                    {
                        "symbol": symbol,
                        "threshold": threshold,
                        "direction": direction,
                        "enabled": True,
                        "checked_at": "",
                        "quote_at": "",
                        "state": "Ainda não avaliado",
                        "triggered_at": "",
                    }
                    for symbol, threshold, direction in (
                        ("ITUB4", "28", "below"),
                        ("PETR4", "45", "above"),
                        ("VALE3", "50", "below"),
                    )
                ],
            )
        connection.execute(
            text("INSERT INTO demo_seed_versions(name) VALUES ('finances_v1')")
        )


def _seed_accounts(engine: Engine) -> None:
    """Upgrade existing sample portfolios once; preserve initialized accounts."""
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    repository = SqlAlchemyTransactionRepository(factory)
    for portfolio in portfolios.list_all():
        if portfolio.id is None or portfolio.name not in {
            "Longo Prazo",
            "Dividendos",
            "Crescimento",
        }:
            continue
        trades, existing = repository.read_ledger(portfolio.id)
        if existing or not trades:
            continue
        start = min(t.occurred_at for t in trades) - timedelta(days=1)
        end = max(t.occurred_at for t in trades) + timedelta(days=1)
        capital = sum(
            (
                t.amounts()[1]
                for t in trades
                if t.transaction_type == TransactionType.BUY
            ),
            Decimal(0),
        )
        events = (
            PortfolioEvent(
                portfolio.id,
                PortfolioEventType.OPENING,
                start,
                capital,
                note="Capital inicial do exemplo",
            ),
            PortfolioEvent(
                portfolio.id,
                PortfolioEventType.DEPOSIT,
                start + timedelta(hours=1),
                Decimal(10000),
                note="Aporte adicional",
            ),
            PortfolioEvent(
                portfolio.id,
                PortfolioEventType.DIVIDEND,
                end,
                Decimal(840),
                asset=trades[0].asset,
                note="Proventos do exemplo",
            ),
            PortfolioEvent(
                portfolio.id,
                PortfolioEventType.JCP,
                end,
                Decimal(425),
                withholding=Decimal("63.75"),
                asset=trades[0].asset,
            ),
            PortfolioEvent(
                portfolio.id, PortfolioEventType.WITHDRAWAL, end, Decimal(1500)
            ),
            PortfolioEvent(portfolio.id, PortfolioEventType.FEE, end, Decimal(25)),
            PortfolioEvent(portfolio.id, PortfolioEventType.TAX, end, Decimal(110)),
        )
        cash_state(trades, events)
        with engine.begin() as connection:
            # Atomic per account, including interruption/restart during first launch.
            if connection.execute(
                select(PortfolioEventModel.id)
                .where(PortfolioEventModel.portfolio_id == portfolio.id)
                .limit(1)
            ).first():
                continue
            connection.execute(
                insert(PortfolioEventModel),
                [
                    {
                        "portfolio_id": e.portfolio_id,
                        "kind": e.kind.value,
                        "occurred_at": e.occurred_at.isoformat(),
                        "amount": str(e.amount),
                        "withholding": str(e.withholding),
                        "asset_symbol": e.asset.symbol if e.asset else None,
                        "ratio": None,
                        "currency": e.currency,
                        "note": e.note,
                    }
                    for e in events
                ],
            )
