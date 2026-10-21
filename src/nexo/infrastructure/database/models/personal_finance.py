from sqlalchemy import Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from nexo.infrastructure.database.models.portfolio_model import Base


class BudgetModel(Base):
    __tablename__ = "budget_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    amount: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    month: Mapped[str] = mapped_column(Text)


class GoalModel(Base):
    __tablename__ = "financial_goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(Text)
    current: Mapped[str] = mapped_column(Text)
    deadline: Mapped[str] = mapped_column(Text)


class AlertModel(Base):
    __tablename__ = "price_alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(Text)
    threshold: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean)
    checked_at: Mapped[str] = mapped_column(Text)
    quote_at: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    triggered_at: Mapped[str] = mapped_column(Text)
