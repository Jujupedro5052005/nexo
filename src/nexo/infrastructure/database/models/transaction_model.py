from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from nexo.infrastructure.database.models.portfolio_model import Base


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = {"sqlite_autoincrement": True}  # noqa: RUF012 -- SQLAlchemy class configuration

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False, index=True
    )
    asset_symbol: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_type: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price: Mapped[str] = mapped_column(Text, nullable=False)
    fees: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[str] = mapped_column(Text, nullable=False)
