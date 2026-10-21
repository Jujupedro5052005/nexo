from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nexo.domain.interfaces.personal_finance_repository import PersonalFinanceError
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal, PriceAlert
from nexo.infrastructure.database.models.personal_finance import (
    AlertModel,
    BudgetModel,
    GoalModel,
)


class SqlPersonalFinanceRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def _rows(self, model: Any) -> list[dict[str, Any]]:
        try:
            with self._sessions() as session:
                return [
                    {
                        column.name: getattr(row, column.name)
                        for column in model.__table__.columns
                    }
                    for row in session.scalars(select(model).order_by(model.id))
                ]
        except SQLAlchemyError:
            raise PersonalFinanceError(
                "Não foi possível ler os dados locais."
            ) from None

    def _save(self, model: Any, record: Any) -> None:
        values = asdict(record)
        identity = values.pop("id")
        values = {
            key: str(value) if isinstance(value, (Decimal, date)) else value
            for key, value in values.items()
        }
        try:
            with self._sessions.begin() as session:
                row = session.get(model, identity) if identity is not None else None
                if identity is not None and row is None:
                    raise PersonalFinanceError(
                        "Registro não encontrado. Atualize a página."
                    )
                if row is None:
                    session.add(model(**values))
                else:
                    for key, value in values.items():
                        setattr(row, key, value)
        except SQLAlchemyError:
            raise PersonalFinanceError(
                "Não foi possível salvar os dados locais."
            ) from None

    def budget_entries(self) -> tuple[BudgetEntry, ...]:
        return tuple(
            BudgetEntry(
                **{
                    **r,
                    "amount": Decimal(r["amount"]),
                    "month": date.fromisoformat(r["month"]),
                }
            )
            for r in self._rows(BudgetModel)
        )

    def save_budget(self, entry: BudgetEntry) -> None:
        self._save(BudgetModel, entry)

    def goals(self) -> tuple[FinancialGoal, ...]:
        return tuple(
            FinancialGoal(
                **{
                    **r,
                    "target": Decimal(r["target"]),
                    "current": Decimal(r["current"]),
                    "deadline": date.fromisoformat(r["deadline"]),
                }
            )
            for r in self._rows(GoalModel)
        )

    def save_goal(self, goal: FinancialGoal) -> None:
        self._save(GoalModel, goal)

    def alerts(self) -> tuple[PriceAlert, ...]:
        return tuple(
            PriceAlert(**{**r, "threshold": Decimal(r["threshold"])})
            for r in self._rows(AlertModel)
        )

    def save_alert(self, alert: PriceAlert) -> None:
        self._save(AlertModel, alert)
