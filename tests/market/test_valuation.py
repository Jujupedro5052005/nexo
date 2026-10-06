from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext

import pytest

from nexo.calculations.valuation.portfolio import value_portfolio
from nexo.domain.interfaces.market_data_provider import (
    MarketDataUnavailableError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.domain.models.position import Position
from nexo.domain.reconstruction import ReconstructionResult

D = Decimal
NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)


def position(**changes):
    return replace(
        Position(1, Asset("PETR4"), D("15"), D("35.2"), D("528"), D("33")), **changes
    )


def quote(price="40", currency="BRL", symbol="PETR4"):
    return Quote(Asset(symbol), D(price), currency, symbol, NOW, NOW)


def test_required_valuation_example_and_separate_realized_result():
    value = value_portfolio(
        ReconstructionResult((position(),), ()), QuoteBatch((quote(),))
    )
    assert value.invested_cost == D("528")
    assert value.current_market_value == D("600")
    assert value.unrealized_profit_loss == D("72")
    assert value.realized_profit_loss == D("33")
    assert value.total_profit_loss == D("105")
    assert value.unrealized_return == value.positions[0].unrealized_return
    assert abs(value.unrealized_return - D("72") / D("528")) < D("1e-27")


@pytest.mark.parametrize(
    "price,market,pnl,total",
    [
        ("30", "450", "-78", "-45"),
        ("35.2", "528", "0", "33"),
        ("50", "750", "222", "255"),
    ],
)
def test_gain_loss_and_unchanged_cost(price, market, pnl, total):
    value = value_portfolio(
        ReconstructionResult((position(),), ()), QuoteBatch((quote(price),))
    )
    assert value.current_market_value == D(
        market
    ) and value.unrealized_profit_loss == D(pnl)
    assert value.total_profit_loss == D(total) and value.invested_cost == D("528")


def test_closed_result_survives_without_requesting_its_quote():
    closed = position(quantity=D(0), average_cost=D(0), cost_basis=D(0))
    value = value_portfolio(ReconstructionResult((), (closed,)), QuoteBatch(()))
    assert value.current_market_value == 0 and value.unrealized_profit_loss == 0
    assert value.realized_profit_loss == value.total_profit_loss == 33
    assert value.unrealized_return is None and value.positions == ()


def test_empty_portfolio_has_mathematical_zero_values_and_no_percentage():
    value = value_portfolio(ReconstructionResult((), ()), QuoteBatch(()))
    assert value.complete and value.current_market_value == value.total_profit_loss == 0
    assert value.unrealized_return is None


def test_missing_quote_never_turns_into_zero_or_hides_ledger():
    error = MarketDataUnavailableError("Sem rede")
    value = value_portfolio(
        ReconstructionResult((position(),), ()),
        QuoteBatch((), (QuoteIssue(Asset("PETR4"), error),)),
    )
    assert not value.complete and value.current_market_value is None
    assert (
        value.unrealized_profit_loss
        is value.total_profit_loss
        is value.unrealized_return
        is None
    )
    assert value.invested_cost == 528 and value.realized_profit_loss == 33
    assert value.positions[0].unavailable_reason == "Sem rede"


def test_partial_quotes_keep_available_rows_but_not_partial_aggregate():
    other = position(asset=Asset("VALE3"))
    value = value_portfolio(
        ReconstructionResult((position(), other), ()), QuoteBatch((quote(),))
    )
    assert value.positions[0].market_value == 600
    assert (
        value.positions[1].market_value is None and value.current_market_value is None
    )
    assert value.invested_cost == 1056 and value.realized_profit_loss == 66


@pytest.mark.parametrize("currency", ["USD", "EUR", "JPY"])
def test_no_fictional_currency_conversion_or_mixed_aggregate(currency):
    value = value_portfolio(
        ReconstructionResult((position(),), ()), QuoteBatch((quote(currency=currency),))
    )
    row = value.positions[0]
    assert row.quote.currency == currency and row.market_value == 600
    assert row.unrealized_profit_loss is None and value.current_market_value is None
    assert "sem conversão" in row.unavailable_reason


def test_valuation_is_independent_of_global_decimal_precision():
    p = position(
        quantity=D("1.123456789012345678901234567890"),
        average_cost=D("1"),
        cost_basis=D("1.123456789012345678901234567890"),
    )
    result = ReconstructionResult((p,), ())
    batch = QuoteBatch((quote("123456789.01234567890123456789"),))
    baseline = value_portfolio(result, batch)
    with localcontext() as context:
        context.prec = 4
        context.rounding = "ROUND_UP"
        assert value_portfolio(result, batch) == baseline
    with localcontext() as context:
        context.prec = 100
        assert baseline.current_market_value == p.quantity * batch.quotes[0].price


def test_three_distinct_assets_match_quotes_by_asset_not_response_order():
    vale = position(
        asset=Asset("VALE3"),
        quantity=D(2),
        average_cost=D(50),
        cost_basis=D(100),
        realized_profit_loss=D(-5),
    )
    itub = position(
        asset=Asset("ITUB4"),
        quantity=D(3),
        average_cost=D(10),
        cost_basis=D(30),
        realized_profit_loss=D(7),
    )
    result = ReconstructionResult((position(), vale, itub), ())
    batch = QuoteBatch(
        (quote("12", symbol="ITUB4"), quote("60", symbol="VALE3"), quote("40"))
    )
    value = value_portfolio(result, batch)
    assert [item.market_value for item in value.positions] == [D(600), D(120), D(36)]
    assert value.invested_cost == 658 and value.current_market_value == 756
    assert value.realized_profit_loss == 35 and value.unrealized_profit_loss == 98
    assert value.total_profit_loss == 133
