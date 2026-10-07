from collections.abc import Iterable
from decimal import Context, Decimal


def financial_context(values: Iterable[Decimal | None], *, count: int = 1) -> Context:
    numbers = [n for n in values if n is not None]
    span = (
        max((n.adjusted() for n in numbers), default=0)
        - min((int(n.as_tuple().exponent) for n in numbers), default=0)
        + 1
    )
    return Context(prec=max(50, 2 * span + len(str(count)) + 10))
