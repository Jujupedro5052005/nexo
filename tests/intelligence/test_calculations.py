from decimal import Decimal, localcontext

import pytest

from nexo.calculations.valuation.intelligence import (
    ValuationInputs,
    calculate_valuation,
    sensitivity,
)


def premise(**changes):
    return ValuationInputs.model_validate(
        {
            "method": "gordon",
            "expected_dividend": "3",
            "dividend_source": "manual",
            "sustainability_note": "cenário sintético",
            "required_return": "0.10",
            "growth": "0.04",
            **changes,
        }
    )


def test_known_gordon_and_margins():
    result = calculate_valuation(premise(quote="40"))
    assert result["theoretical_value"] == Decimal(50)
    assert result["ceiling_price"] == Decimal(40)
    assert result["difference_percent"] == Decimal(25)
    assert result["safety_margin"] == Decimal("0.2")
    assert result["assumptions"]["quote"] == "40"


def test_reuses_yield_and_multiples():
    assert (
        calculate_valuation(premise(method="target_yield", target_yield="0.06"))[
            "theoretical_value"
        ]
        == 50
    )
    assert (
        calculate_valuation(
            premise(
                method="multiples",
                metric="eps",
                metric_per_share="4",
                reference_multiple="10",
                comparability_note="pares sintéticos",
            )
        )["theoretical_value"]
        == 40
    )


@pytest.mark.parametrize(
    "change",
    [
        {"growth": "0.10"},
        {"growth": "0.11"},
        {"growth": None},
        {"required_return": None},
        {"expected_dividend": None},
        {"dividend_source": ""},
        {"sustainability_note": " "},
        {"expected_dividend": "NaN"},
        {"expected_dividend": "Infinity"},
        {"quote": "-1"},
        {"quote": "0"},
        {"safety_discount": "1"},
        {"safety_discount": "-0.1"},
        {"method": "target_yield", "target_yield": "0"},
        {"method": "target_yield", "target_yield": None},
        {"method": "multiples", "metric_per_share": "-1"},
        {"method": "multiples", "asset_type": "fii", "metric": "eps"},
        {"asset_type": "crypto"},
        {"asset_type": "bond"},
        {"asset_type": "etf"},
        {"currency": "USD"},
        {"unexpected": "field"},
    ],
)
def test_invalid_boundaries(change):
    with pytest.raises(ValueError):
        premise(**change)


def test_zero_dividend_is_explicit_not_missing():
    result = calculate_valuation(premise(expected_dividend="0", quote="30"))
    assert result["theoretical_value"] == 0
    assert result["safety_margin"] is None
    assert result["quote"] == 30


def test_missing_quote_and_sensitivity():
    inputs = premise()
    assert calculate_valuation(inputs)["difference_percent"] is None
    points = sensitivity(inputs)
    assert len(points) == 5
    assert points[2]["input"] == Decimal("0.10")
    assert points[2]["ceiling_price"] == 40
    assert points[0]["ceiling_price"] > points[4]["ceiling_price"]
    assert sensitivity(premise(growth="0.099"))[0]["available"] is False


def test_precision_is_independent_of_callers_context():
    with localcontext() as ctx:
        ctx.prec = 3
        assert calculate_valuation(premise())["theoretical_value"] == 50


def test_extreme_decimal_exponents_cannot_allocate_unbounded_precision():
    with pytest.raises(ValueError, match="12 casas"):
        premise(required_return="1e-999999999", growth="0")
