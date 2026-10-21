from pathlib import Path
from sqlite3 import Connection

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nexo.core.paths import application_data_dir
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.infrastructure.database.models import (
    personal_finance,  # noqa: F401 -- register implemented tables
    portfolio_event,  # noqa: F401 -- append-only cash and corporate events
)
from nexo.infrastructure.database.models.transaction_model import TransactionModel


def default_database_path() -> Path:
    """Use the source checkout's data directory, independent of process cwd."""
    return application_data_dir() / "nexo.db"


def create_database_engine(database_path: Path | None = None) -> Engine:
    path = (database_path or default_database_path()).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            URL.create("sqlite+pysqlite", database=str(path)),
            connect_args={"timeout": 10},
        )
        event.listen(engine, "connect", _enable_foreign_keys)
        return engine
    except (OSError, SQLAlchemyError) as error:
        raise PortfolioRepositoryError(
            "Não foi possível preparar o banco local."
        ) from error


def initialize_database(engine: Engine) -> None:
    """Create only the implemented schema; do not erase existing data."""
    try:
        TransactionModel.metadata.create_all(engine)
    except SQLAlchemyError as error:
        raise PortfolioRepositoryError(
            "Não foi possível preparar o banco local."
        ) from error


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def _enable_foreign_keys(connection: Connection, _record: object) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=10000")
    finally:
        cursor.close()
