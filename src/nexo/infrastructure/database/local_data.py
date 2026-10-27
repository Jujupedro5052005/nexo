import os
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from nexo.application.local_data import LocalDataError
from nexo.infrastructure.database.models.portfolio_model import Base


class SqliteLocalDataStorage:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.path = Path(str(engine.url.database)).resolve()

    @property
    def location(self) -> str:
        return str(self.path)

    def backup(self, destination: Path) -> None:
        destination = destination.resolve()
        if destination == self.path or destination in (
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
        ):
            raise LocalDataError("Escolha um arquivo diferente do banco em uso.")
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                dir=destination.parent, suffix=".db", delete=False
            ) as file:
                temporary = Path(file.name)
            with (
                closing(sqlite3.connect(self.path)) as source,
                closing(sqlite3.connect(temporary)) as target,
            ):
                source.backup(target)
            os.replace(temporary, destination)
        except (OSError, sqlite3.Error) as error:
            raise LocalDataError("Não foi possível exportar o banco local.") from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def clear(self) -> Path:
        # UI quiesces its workers before invoking this operation. No source file is removed.
        backup = self.path.with_name(f"{self.path.stem}_backup_{uuid4().hex}.db")
        try:
            with self.engine.begin() as connection:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                self.backup(backup)
                for table in reversed(Base.metadata.sorted_tables):
                    connection.execute(table.delete())
        except SQLAlchemyError as error:
            raise LocalDataError(
                "Não foi possível limpar os dados. O banco foi preservado."
            ) from error
        return backup
