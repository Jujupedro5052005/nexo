from decimal import Decimal

import pytest

from nexo.ui.decimal_parser import DecimalInputError, parse_decimal


@pytest.mark.parametrize(
    "text, expected",
    [
        ("10", "10"),
        ("10.50", "10.50"),
        ("10,50", "10.50"),
        ("0.5", "0.5"),
        ("0,5", "0.5"),
        ("0.25", "0.25"),
        ("0,25", "0.25"),
        ("1.234,56", "1234.56"),
        ("1.234.567,89", "1234567.89"),
        ("1.234", "1.234"),
        (" 10,50 ", "10.50"),
        ("0.3333333333333333333333333333", "0.3333333333333333333333333333"),
    ],
)
def test_parser_accepts_documented_grammar(text, expected) -> None:
    result = parse_decimal(text)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "abc",
        "NaN",
        "Infinity",
        "-Infinity",
        "-1",
        "1,234.56",
        "12.34,56",
        "1.234.56",
        "1,2,3",
        "1e3",
        "R$ 10",
        "1 234",
        "+1",
    ],
)
def test_parser_rejects_invalid_or_ambiguous_input(text) -> None:
    with pytest.raises(DecimalInputError):
        parse_decimal(text, allow_zero=True)


@pytest.mark.parametrize("text", ["0", "0,00", "0.00"])
def test_zero_is_only_allowed_for_fees(text) -> None:
    assert parse_decimal(text, allow_zero=True) == 0
    with pytest.raises(DecimalInputError):
        parse_decimal(text)
