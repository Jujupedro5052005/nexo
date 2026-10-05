from pathlib import Path

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.infrastructure.database.models.portfolio_model import Base


def default_database_path() -> Path:
    """Use the source checkout's data directory, independent of process cwd."""
    return Path(__file__).resolve().parents[4] / "data" / "nexo.db"


def create_database_engine(database_path: Path | None = None) -> Engine:
    path = (database_path or default_database_path()).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(URL.create("sqlite+pysqlite", database=str(path)))
    except (OSError, SQLAlchemyError) as error:
        raise PortfolioRepositoryError("Não foi possível preparar o banco local.") from error


def initialize_database(engine: Engine) -> None:
    """Create only the implemented schema; do not erase existing data."""
    try:
        Base.metadata.create_all(engine)
    except SQLAlchemyError as error:
        raise PortfolioRepositoryError("Não foi possível preparar o banco local.") from error


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)
