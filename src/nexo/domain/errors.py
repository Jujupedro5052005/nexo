class DomainValidationError(ValueError):
    """A financial object or history violates a domain invariant."""


class InsufficientPositionError(DomainValidationError):
    """A sale exceeds the available quantity for its portfolio and asset."""
