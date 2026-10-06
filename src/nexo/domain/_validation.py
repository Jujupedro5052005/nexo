from decimal import Decimal

from nexo.domain.errors import DomainValidationError


def validate_identity(value: int, field: str) -> None:
    if type(value) is not int or value <= 0:
        raise DomainValidationError(f"{field} must be a positive integer.")


def validate_decimal(value: Decimal, field: str, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal):
        raise DomainValidationError(f"{field} must be Decimal.")
    if not value.is_finite():
        raise DomainValidationError(f"{field} must be finite.")
    if value < 0 or (positive and value == 0):
        constraint = "positive" if positive else "nonnegative"
        raise DomainValidationError(f"{field} must be {constraint}.")
