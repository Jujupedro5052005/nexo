from dataclasses import dataclass

from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class Asset:
    """Immutable value object identified by its normalized symbol."""

    symbol: str

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str):
            raise DomainValidationError("symbol must be a string.")
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise DomainValidationError("symbol must not be empty.")
        object.__setattr__(self, "symbol", symbol)
