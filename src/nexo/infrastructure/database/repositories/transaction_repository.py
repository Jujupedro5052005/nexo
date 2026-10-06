from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nexo.domain._validation import validate_identity
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.transaction_repository import (
    TransactionRepository,
    TransactionRepositoryError,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import order_transactions
from nexo.infrastructure.database.models.transaction_model import TransactionModel


def _to_domain(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        portfolio_id=model.portfolio_id,
        asset=Asset(model.asset_symbol),
        transaction_type=TransactionType(model.transaction_type),
        quantity=Decimal(model.quantity),
        unit_price=Decimal(model.unit_price),
        fees=Decimal(model.fees),
        occurred_at=datetime.fromisoformat(model.occurred_at),
    )


class SqlAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, transaction: Transaction) -> Transaction:
        if transaction.id is not None:
            raise DomainValidationError("A transação já possui identidade persistida.")
        try:
            with self._session_factory.begin() as session:
                model = TransactionModel(
                    portfolio_id=transaction.portfolio_id,
                    asset_symbol=transaction.asset.symbol,
                    transaction_type=transaction.transaction_type.value,
                    quantity=str(transaction.quantity),
                    unit_price=str(transaction.unit_price),
                    fees=str(transaction.fees),
                    occurred_at=transaction.occurred_at.isoformat(),
                )
                session.add(model)
                session.flush()
                persisted = _to_domain(model)
            return persisted
        except SQLAlchemyError as error:
            raise TransactionRepositoryError(
                "Não foi possível salvar a movimentação."
            ) from error

    def list_by_portfolio(self, portfolio_id: int) -> list[Transaction]:
        validate_identity(portfolio_id, "portfolio_id")
        try:
            with self._session_factory() as session:
                models = session.scalars(
                    select(TransactionModel)
                    .where(TransactionModel.portfolio_id == portfolio_id)
                    .order_by(TransactionModel.id)
                )
                return order_transactions(_to_domain(model) for model in models)
        except (SQLAlchemyError, ValueError, ArithmeticError) as error:
            raise TransactionRepositoryError(
                "Não foi possível carregar as movimentações."
            ) from error
