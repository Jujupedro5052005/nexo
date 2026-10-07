from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext

import pytest

from nexo.calculations.indicators.fundamentals import (
    annual_dividend,
    dividend_window,
    fundamental_indicators,
)
from nexo.calculations.risk.history import historical_risk
from nexo.calculations.valuation.company import bazin_price, graham_price, safety_margin
from nexo.calculations.valuation.portfolio import value_portfolio
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.market_data_provider import QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory, Quote
from nexo.domain.models.position import Position
from nexo.domain.reconstruction import ReconstructionResult

D = Decimal
NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
ASSET = Asset("PETR4")


def fundamentals(**changes):
    return replace(
        CompanyFundamentals(
            ASSET,
            NOW,
            eps=D(4),
            bvps=D(20),
            roe=D("0.2"),
            roa=D("0.1"),
            net_margin=D("0.25"),
            revenue=D(1000),
            ebitda=D(300),
            debt=D(200),
            cash=D(100),
        ),
        **changes,
    )


def quote(price=80, currency="BRL", symbol="PETR4"):
    return Quote(Asset(symbol), D(price), currency, symbol, NOW)


def history(prices):
    return PriceHistory(
        ASSET,
        tuple(
            HistoricalPrice(NOW + timedelta(days=i), D(price))
            for i, price in enumerate(prices)
        ),
        "1mo",
        NOW,
    )


def test_graham_classic_formula_with_decimal_square_root():
    with localcontext() as context:
        context.prec = 70
        expected = D(1800).sqrt()
    assert abs(graham_price(D(4), D(20)) - expected) < D("1e-47")


@pytest.mark.parametrize(
    "eps,bvps",
    [
        (None, D(20)),
        (D(4), None),
        (D(0), D(20)),
        (D(-4), D(20)),
        (D(4), D(0)),
        (D(4), D(-20)),
        (D("NaN"), D(20)),
        (D("Infinity"), D(20)),
        (4.0, D(20)),
    ],
)
def test_graham_unavailable_for_invalid_inputs_without_abs(eps, bvps):
    assert graham_price(eps, bvps) is None


def test_bazin_explicit_premise_example():
    assert bazin_price(D(6), D("0.06")) == D(100)
    assert bazin_price(D(6), D("0.12")) == D(50)


@pytest.mark.parametrize("yield_value", [D(0), D(-1), D("NaN"), D("Infinity"), 0.06])
def test_bazin_rejects_invalid_yield(yield_value):
    with pytest.raises(DomainValidationError):
        bazin_price(D(6), yield_value)


@pytest.mark.parametrize("dividend", [None, D(0), D(-1), D("NaN")])
def test_bazin_missing_or_nonpositive_dividend_is_not_a_fair_price(dividend):
    assert bazin_price(dividend, D("0.06")) is None


@pytest.mark.parametrize(
    "current,ratio,difference",
    [(80, "0.2", 20), (120, "-0.2", -20), (100, "0", 0), (0, "1", 100)],
)
def test_safety_margin_has_absolute_and_ratio_values(current, ratio, difference):
    margin = safety_margin(D(100), D(current))
    assert margin.difference == difference and margin.ratio == D(ratio)


@pytest.mark.parametrize(
    "fair,current",
    [
        (None, D(80)),
        (D(0), D(80)),
        (D(-100), D(80)),
        (D(100), None),
        (D(100), D(-1)),
        (D("NaN"), D(80)),
    ],
)
def test_invalid_safety_margin_is_unavailable(fair, current):
    assert safety_margin(fair, current) is None


def test_indicators_calculated_and_supplied_origins_are_explicit():
    values = {i.key: i for i in fundamental_indicators(fundamentals(), quote(), D(6))}
    assert values["pe"].value == 20 and values["pb"].value == 4
    assert values["dy"].value == D("0.075")
    assert values["roe"].value == D("0.2") and "financial-data" in values["roe"].origin
    assert values["roa"].value == D("0.1") and values["net_margin"].value == D("0.25")
    assert values["ebitda_margin"].value == D("0.3")
    assert abs(values["leverage"].value - D(1) / D(3)) < D("1e-27")
    assert all(i.formula and i.origin for i in values.values())


@pytest.mark.parametrize(
    "changes,missing",
    [
        ({"eps": D(0)}, "pe"),
        ({"eps": D(-4)}, "pe"),
        ({"bvps": None}, "pb"),
        ({"bvps": D(0)}, "pb"),
        ({"bvps": D(-1)}, "pb"),
        ({"revenue": D(0)}, "ebitda_margin"),
        ({"revenue": None}, "ebitda_margin"),
        ({"ebitda": D(0)}, "leverage"),
        ({"ebitda": D(-1)}, "leverage"),
        ({"cash": None}, "leverage"),
        ({"debt": D(-1)}, "leverage"),
    ],
)
def test_indicators_missing_zero_and_negative_denominators(changes, missing):
    values = {
        i.key: i for i in fundamental_indicators(fundamentals(**changes), quote(), D(6))
    }
    assert values[missing].value is None and values[missing].reason


def test_negative_provider_ratios_and_net_cash_are_preserved():
    values = {
        i.key: i.value
        for i in fundamental_indicators(
            fundamentals(roe=D("-0.1"), cash=D(500)), quote(), D(0)
        )
    }
    assert values["roe"] == D("-0.1") and values["leverage"] == -1
    assert values["dy"] == 0


def test_missing_inputs_and_incompatible_currency_do_not_become_zero():
    values = {i.key: i.value for i in fundamental_indicators(None, None, None)}
    assert all(value is None for value in values.values())
    values = {
        i.key: i.value
        for i in fundamental_indicators(fundamentals(), quote(currency="USD"), D(6))
    }
    assert values["pe"] is values["pb"] is values["dy"] is None
    assert values["roe"] == D("0.2")


def test_annual_dividend_policy_excludes_future_unverified_and_optional_jcp():
    summary = DividendSummary(
        ASSET,
        (
            CashDividend(date(2026, 1, 1), D(6), "DIVIDENDO", True),
            CashDividend(date(2026, 2, 1), D(2), "JCP", True),
            CashDividend(date(2026, 3, 1), D(100), "DIVIDENDO", False),
            CashDividend(date(2027, 1, 1), D(100), "DIVIDENDO", True),
        ),
        date(2025, 10, 7),
        date(2026, 10, 6),
        NOW,
    )
    assert (
        annual_dividend(summary) == 6
        and annual_dividend(summary, include_jcp=True) == 8
    )
    assert annual_dividend(None) is None
    assert annual_dividend(replace(summary, events=())) == 0


@pytest.mark.parametrize(
    "as_of,start",
    [
        (date(2026, 10, 6), date(2025, 10, 7)),
        (date(2024, 2, 29), date(2023, 3, 1)),
        (date(2025, 2, 28), date(2024, 2, 29)),
    ],
)
def test_dividend_window_is_calendar_year_with_explicit_boundary(as_of, start):
    assert dividend_window(as_of) == (start, as_of)


def test_sample_volatility_and_annualization_have_explicit_252_basis():
    risk = historical_risk(history([100, 110, 99]))
    with localcontext() as context:
        context.prec = 70
        assert abs(risk.daily_volatility - D("0.02").sqrt()) < D("1e-47")
        assert abs(risk.annual_volatility - D("5.04").sqrt()) < D("1e-46")
    assert risk.trading_days == 252 and risk.max_drawdown == D("-0.1")


def test_drawdown_is_asset_running_peak_and_volatility_can_be_zero():
    assert historical_risk(history([100, 120, 90, 110])).max_drawdown == D("-0.25")
    risk = historical_risk(history([100, 110, 121]))
    assert (
        risk.daily_volatility == risk.annual_volatility == 0 and risk.max_drawdown == 0
    )


@pytest.mark.parametrize("prices", [[], [100]])
def test_risk_missing_observations_is_unavailable(prices):
    risk = historical_risk(history(prices))
    assert risk.daily_volatility is risk.annual_volatility is risk.max_drawdown is None


def test_two_prices_allow_drawdown_but_not_sample_volatility():
    risk = historical_risk(history([100, 80]))
    assert risk.max_drawdown == D("-0.2") and risk.daily_volatility is None


def test_risk_rejects_duplicate_dates_and_invalid_annualization():
    h = history([100, 110, 99])
    h = replace(h, points=(h.points[0], h.points[0], h.points[2]))
    assert historical_risk(h).max_drawdown is None
    with pytest.raises(DomainValidationError):
        historical_risk(h, trading_days=0)


def test_three_positions_concentration_weights_top3_and_hhi():
    positions = tuple(
        Position(1, Asset(symbol), D(1), D(10), D(10), D(0))
        for symbol in ("PETR4", "VALE3", "ITUB4")
    )
    value = value_portfolio(
        ReconstructionResult(positions, ()),
        QuoteBatch((quote(50), quote(30, symbol="VALE3"), quote(20, symbol="ITUB4"))),
    )
    result = value.concentration
    assert [p.weight for p in result.weights] == [D("0.5"), D("0.3"), D("0.2")]
    assert (
        result.largest == D("0.5") and result.top_three == 1 and result.hhi == D("0.38")
    )


def test_concentration_missing_quote_empty_and_currency_are_not_partial_weights():
    p = Position(1, ASSET, D(1), D(10), D(10), D(0))
    for batch in (QuoteBatch(()), QuoteBatch((quote(currency="USD"),))):
        c = value_portfolio(ReconstructionResult((p,), ()), batch).concentration
        assert c.weights == () and c.largest is c.top_three is c.hhi is None
        assert c.unavailable_assets == ("PETR4",)
    assert (
        value_portfolio(
            ReconstructionResult((), ()), QuoteBatch(())
        ).concentration.largest
        is None
    )


def test_financial_formulas_do_not_depend_on_global_precision():
    baseline = (
        graham_price(D(4), D(20)),
        bazin_price(D(6), D("0.06")),
        safety_margin(D(100), D(80)),
        historical_risk(history([100, 120, 90, 110])),
    )
    with localcontext() as context:
        context.prec = 3
        context.rounding = "ROUND_UP"
        assert (
            graham_price(D(4), D(20)),
            bazin_price(D(6), D("0.06")),
            safety_margin(D(100), D(80)),
            historical_risk(history([100, 120, 90, 110])),
        ) == baseline
