from pathlib import Path
from typing import Protocol


class LocalDataError(Exception):
    """Safe failure of a local database maintenance operation."""


class LocalDataStorage(Protocol):
    @property
    def location(self) -> str: ...

    def backup(self, destination: Path) -> None: ...

    def clear(self) -> Path: ...


class ManageLocalData:
    """Coordinate complete SQLite exports and reset with a mandatory backup."""

    def __init__(self, storage: LocalDataStorage) -> None:
        self.storage = storage

    @property
    def location(self) -> str:
        return self.storage.location

    def export(self, destination: str) -> None:
        self.storage.backup(Path(destination))

    def clear(self) -> Path:
        return self.storage.clear()
