import re
from decimal import Decimal


class DecimalInputError(ValueError):
    """A numeric input cannot be interpreted under the documented UI grammar."""


def parse_decimal(text: str, *, allow_zero: bool = False) -> Decimal:
    """Accept decimal dot/comma; Brazilian grouping requires a decimal comma.

    A single dot always means decimal (1.234 = 1.234). No exponent notation,
    currency prefixes, signs or whitespace within a number are accepted.
    """
    value = text.strip()
    if re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]+", value):
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[0-9]+(?:[.,][0-9]+)?", value):
        value = value.replace(",", ".")
    else:
        raise DecimalInputError("Informe um número válido, como 10,50 ou 1.234,56.")
    number = Decimal(value)
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        rule = "maior ou igual a zero" if allow_zero else "maior que zero"
        raise DecimalInputError(f"O valor deve ser {rule}.")
    return number
