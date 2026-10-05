from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nexo.domain.interfaces.portfolio_repository import (
    PortfolioRepository,
    PortfolioRepositoryError,
)
from nexo.domain.models.portfolio import Portfolio
from nexo.infrastructure.database.models.portfolio_model import PortfolioModel


class SqlAlchemyPortfolioRepository(PortfolioRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, portfolio: Portfolio) -> Portfolio:
        if portfolio.id is not None:
            raise ValueError("A carteira já possui identidade persistida.")
        try:
            with self._session_factory.begin() as session:
                model = PortfolioModel(name=portfolio.name)
                session.add(model)
                session.flush()
                persisted = Portfolio(id=model.id, name=model.name)
            return persisted
        except SQLAlchemyError as error:
            raise PortfolioRepositoryError("Não foi possível salvar a carteira.") from error

    def list_all(self) -> list[Portfolio]:
        try:
            with self._session_factory() as session:
                models = session.scalars(select(PortfolioModel).order_by(PortfolioModel.id))
                return [Portfolio(id=model.id, name=model.name) for model in models]
        except SQLAlchemyError as error:
            raise PortfolioRepositoryError("Não foi possível carregar as carteiras.") from error
