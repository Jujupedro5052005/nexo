from decimal import Decimal


class DomainValidationError(ValueError):
    """A financial object or history violates a domain invariant."""


class InsufficientPositionError(DomainValidationError):
    """A sale exceeds the available quantity for its portfolio and asset."""

    def __init__(
        self, portfolio_id: int, symbol: str, available: Decimal, requested: Decimal
    ) -> None:
        self.portfolio_id = portfolio_id
        self.symbol = symbol
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient position: portfolio {portfolio_id}, {symbol}, "
            f"available {available}, requested {requested}."
        )
