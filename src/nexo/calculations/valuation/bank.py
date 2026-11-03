"""Stable excess-return valuation; clean-surplus and constant ROE are assumptions."""

from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context


def bank_residual_value(
    bvps: Decimal, roe: Decimal, required_return: Decimal, growth: Decimal
) -> Decimal:
    values = (bvps, roe, required_return, growth)
    if any(
        not isinstance(v, Decimal)
        or not v.is_finite()
        or abs(v) > Decimal("1e12")
        or int(v.as_tuple().exponent) < -12
        for v in values
    ):
        raise ValueError("Parâmetros finitos de até 12 casas necessários.")
    if (
        bvps <= 0
        or required_return <= growth
        or required_return <= 0
        or growth <= -1
        or roe < growth
    ):
        raise ValueError("Exige VPA > 0, Ke > g e ROE >= g sustentável.")
    with localcontext(financial_context(values)):
        return bvps * (roe - growth) / (required_return - growth)
