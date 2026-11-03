"""Manual tax scenario; contains no statutory classification, rates or exemptions."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.domain._validation import validate_decimal
from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True)
class TaxScenario:
    taxable_base: Decimal
    compensated_loss: Decimal
    remaining_loss: Decimal
    estimated_tax: Decimal
    payable: Decimal


def manual_tax_scenario(
    profit: Decimal, previous_loss: Decimal, rate: Decimal, withholding: Decimal
) -> TaxScenario:
    if not isinstance(profit, Decimal) or not profit.is_finite():
        raise DomainValidationError("Resultado deve ser decimal finito.")
    validate_decimal(abs(profit), "profit")
    for name, value in (
        ("previous_loss", previous_loss),
        ("rate", rate),
        ("withholding", withholding),
    ):
        validate_decimal(value, name)
    if rate > 1 or any(
        abs(v) > Decimal("1e15") or int(v.as_tuple().exponent) < -12
        for v in (profit, previous_loss, withholding, rate)
    ):
        raise DomainValidationError(
            "Confira alíquota (0–100%) e magnitude dos valores."
        )
    with localcontext() as ctx:
        ctx.prec = 50
        compensated = min(max(profit, Decimal(0)), previous_loss)
        base = max(profit - compensated, Decimal(0))
        tax = (base * rate).quantize(Decimal("0.01"))
        return TaxScenario(
            base,
            compensated,
            previous_loss - compensated + max(-profit, Decimal(0)),
            tax,
            max(tax - withholding, Decimal(0)),
        )
