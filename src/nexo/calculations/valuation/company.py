from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.errors import DomainValidationError


def _valid(value: Decimal | None) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def graham_price(eps: Decimal | None, bvps: Decimal | None) -> Decimal | None:
    if (
        not _valid(eps)
        or not _valid(bvps)
        or eps is None
        or bvps is None
        or eps <= 0
        or bvps <= 0
    ):
        return None
    with localcontext(financial_context([eps, bvps])):
        return (Decimal("22.5") * eps * bvps).sqrt()


def bazin_price(
    annual_dividend: Decimal | None, required_yield: Decimal
) -> Decimal | None:
    if not _valid(required_yield) or required_yield <= 0:
        raise DomainValidationError(
            "O yield requerido deve ser Decimal finito e positivo."
        )
    if annual_dividend is None or not _valid(annual_dividend) or annual_dividend <= 0:
        return None
    with localcontext(financial_context([annual_dividend, required_yield])):
        return annual_dividend / required_yield


@dataclass(frozen=True, slots=True)
class SafetyMargin:
    difference: Decimal
    ratio: Decimal


def safety_margin(
    fair_value: Decimal | None, current_price: Decimal | None
) -> SafetyMargin | None:
    if (
        not _valid(fair_value)
        or not _valid(current_price)
        or fair_value is None
        or current_price is None
        or fair_value <= 0
        or current_price < 0
    ):
        return None
    with localcontext(financial_context([fair_value, current_price])):
        difference = fair_value - current_price
        return SafetyMargin(difference, difference / fair_value)
