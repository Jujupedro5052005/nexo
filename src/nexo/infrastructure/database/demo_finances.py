"""Idempotent sample data, restricted to the separate demonstration database."""

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine, insert, select, text

from nexo.infrastructure.database.models.personal_finance import (
    AlertModel,
    BudgetModel,
    GoalModel,
)


def seed_demo_finances(engine: Engine) -> None:
    path = Path(str(engine.url.database))
    if (
        path.name != "nexo_demo.db"
        or path.is_symlink()
        or path.resolve().name != "nexo_demo.db"
    ):
        raise ValueError("Exemplos só podem ser gravados no banco demo.")
    today = datetime.now().astimezone().date()
    with engine.begin() as connection:
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
                        ("DEMO · Renda mensal", "8500", "income"),
                        ("DEMO · Moradia e contas", "2800", "fixed"),
                        ("DEMO · Alimentação e transporte", "1700", "variable"),
                        ("DEMO · Lazer e imprevistos", "700", "variable"),
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
                        ("DEMO · Reserva de emergência", "30000", "18000", 365),
                        ("DEMO · Aporte de longo prazo", "100000", "42000", 1095),
                        ("DEMO · Viagem planejada", "18000", "6500", 540),
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
                        "state": "DEMO · exemplo não avaliado",
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
