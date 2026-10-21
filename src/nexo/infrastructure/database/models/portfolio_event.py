from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from nexo.infrastructure.database.models.portfolio_model import Base


class PortfolioEventModel(Base):
    __tablename__ = "portfolio_events"
    __table_args__ = {"sqlite_autoincrement": True}  # noqa: RUF012 -- SQLAlchemy config
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    kind: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[str] = mapped_column(Text)
    amount: Mapped[str] = mapped_column(Text)
    withholding: Mapped[str] = mapped_column(Text)
    asset_symbol: Mapped[str | None] = mapped_column(Text)
    ratio: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text)
