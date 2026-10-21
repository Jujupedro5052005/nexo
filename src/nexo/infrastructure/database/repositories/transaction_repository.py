from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, text
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
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import order_transactions, rebuild_positions
from nexo.domain.services.cash_ledger import cash_state
from nexo.infrastructure.database.models.portfolio_event import PortfolioEventModel
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

    @staticmethod
    def _events(session: Session, portfolio_id: int) -> tuple[PortfolioEvent, ...]:
        return tuple(
            PortfolioEvent(
                r.portfolio_id,
                PortfolioEventType(r.kind),
                datetime.fromisoformat(r.occurred_at),
                Decimal(r.amount),
                Decimal(r.withholding),
                Asset(r.asset_symbol) if r.asset_symbol else None,
                Decimal(r.ratio) if r.ratio is not None else None,
                r.currency,
                r.note,
                r.id,
            )
            for r in session.scalars(
                select(PortfolioEventModel)
                .where(PortfolioEventModel.portfolio_id == portfolio_id)
                .order_by(PortfolioEventModel.id)
            )
        )

    def list_events(self, portfolio_id: int) -> tuple[PortfolioEvent, ...]:
        validate_identity(portfolio_id, "portfolio_id")
        try:
            with self._session_factory() as session:
                return self._events(session, portfolio_id)
        except (SQLAlchemyError, ValueError, ArithmeticError) as error:
            raise TransactionRepositoryError(
                "Não foi possível carregar os eventos da carteira."
            ) from error

    def read_ledger(
        self, portfolio_id: int
    ) -> tuple[list[Transaction], tuple[PortfolioEvent, ...]]:
        validate_identity(portfolio_id, "portfolio_id")
        try:
            with self._session_factory() as session:
                session.execute(text("BEGIN"))
                trades = order_transactions(
                    _to_domain(r)
                    for r in session.scalars(
                        select(TransactionModel).where(
                            TransactionModel.portfolio_id == portfolio_id
                        )
                    )
                )
                return trades, self._events(session, portfolio_id)
        except (SQLAlchemyError, ValueError, ArithmeticError) as error:
            raise TransactionRepositoryError(
                "Não foi possível carregar o livro financeiro da carteira."
            ) from error

    def add_validated(self, transaction: Transaction) -> Transaction:
        if transaction.id is not None:
            raise DomainValidationError("A transação já possui identidade persistida.")
        try:
            with self._session_factory() as session:
                # Acquire the SQLite writer reservation BEFORE reading the ledger.
                # Concurrent writers validate serially against the last committed state.
                session.execute(text("BEGIN IMMEDIATE"))
                history = [
                    _to_domain(r)
                    for r in session.scalars(
                        select(TransactionModel).where(
                            TransactionModel.portfolio_id == transaction.portfolio_id
                        )
                    )
                ]
                events = self._events(session, transaction.portfolio_id)
                rebuild_positions([*history, transaction], events)
                cash_state([*history, transaction], events)
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
                saved = _to_domain(model)
                session.commit()
                return saved
        except SQLAlchemyError as error:
            raise TransactionRepositoryError(
                "Não foi possível gravar a operação com segurança. Outra instância pode estar escrevendo; tente novamente."
            ) from error

    def add_event(self, event: PortfolioEvent) -> PortfolioEvent:
        from dataclasses import replace

        if event.id is not None:
            raise DomainValidationError("Informe um evento novo, sem ID.")
        try:
            with self._session_factory() as session:
                session.execute(text("BEGIN IMMEDIATE"))
                history = [
                    _to_domain(r)
                    for r in session.scalars(
                        select(TransactionModel).where(
                            TransactionModel.portfolio_id == event.portfolio_id
                        )
                    )
                ]
                previous_events = self._events(session, event.portfolio_id)
                if event.kind == PortfolioEventType.SPLIT and any(
                    e.kind == event.kind
                    and e.asset == event.asset
                    and e.occurred_at.date() == event.occurred_at.date()
                    for e in previous_events
                ):
                    raise DomainValidationError(
                        "Já há desdobramento/grupamento deste ativo nesta data. Confira o registro existente."
                    )
                events = (*previous_events, event)
                rebuild_positions(history, events)
                cash_state(history, events)
                model = PortfolioEventModel(
                    portfolio_id=event.portfolio_id,
                    kind=event.kind.value,
                    occurred_at=event.occurred_at.isoformat(),
                    amount=str(event.amount),
                    withholding=str(event.withholding),
                    asset_symbol=event.asset.symbol if event.asset else None,
                    ratio=str(event.ratio) if event.ratio is not None else None,
                    currency=event.currency,
                    note=event.note,
                )
                session.add(model)
                session.flush()
                saved = replace(event, id=model.id)
                session.commit()
                return saved
        except SQLAlchemyError as error:
            raise TransactionRepositoryError(
                "Não foi possível salvar o evento da carteira."
            ) from error
