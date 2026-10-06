from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal, Inexact, getcontext, localcontext
from itertools import permutations

import pytest

from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions

D = Decimal
START = datetime(2026, 1, 1)  # noqa: DTZ001 -- naive histories are supported


def trade(
    kind="BUY",
    quantity="10",
    price="30",
    fees="0",
    *,
    symbol="PETR4",
    portfolio=1,
    day=0,
    identity=None,
) -> Transaction:
    return Transaction(
        portfolio,
        Asset(symbol),
        TransactionType[kind],
        D(quantity),
        D(price),
        D(fees),
        START + timedelta(days=day),
        identity,
    )


def two_buys() -> list[Transaction]:
    return [trade(fees="2", day=0), trade(price="40", fees="2", day=1)]


@pytest.mark.parametrize(
    "history, expected",
    [
        ([trade()], ("10", "300", "30", "0")),
        ([trade(fees="2")], ("10", "302", "30.2", "0")),
        (two_buys(), ("20", "704", "35.2", "0")),
        (
            two_buys() + [trade("SELL", "5", "42", "1", day=2)],
            ("15", "528", "35.2", "33"),
        ),
        ([trade(), trade("SELL", "5", "20", day=1)], ("5", "150", "30", "-50")),
        (
            [
                trade(quantity="0.5", price="10", fees="0.25"),
                trade(quantity="1.25", price="10.5", day=1),
            ],
            ("1.75", "18.375", "10.5", "0"),
        ),
    ],
)
def test_required_financial_examples(history, expected) -> None:
    result = rebuild_positions(history)
    assert len(result.positions) == 1
    position = result.positions[0]
    assert (
        position.quantity,
        position.cost_basis,
        position.average_cost,
        position.realized_profit_loss,
    ) == tuple(map(D, expected))
    assert result.closed_positions == ()


def test_total_sale_removes_open_position_and_preserves_realized_profit() -> None:
    result = rebuild_positions(
        [trade(quantity="3", price="1", fees="1"), trade("SELL", "3", "2", day=1)]
    )
    assert result.positions == ()
    closed = result.closed_positions[0]
    assert closed.quantity == closed.cost_basis == closed.average_cost == D("0")
    assert closed.realized_profit_loss == D("2")


def test_partial_then_total_sale_consumes_rounding_remainder() -> None:
    result = rebuild_positions(
        [
            trade(quantity="3", price="1", fees="1"),
            trade("SELL", "1", "2", day=1),
            trade("SELL", "2", "2", day=2),
        ]
    )
    closed = result.closed_positions[0]
    assert closed.cost_basis == closed.average_cost == closed.quantity == D("0")
    assert closed.realized_profit_loss == D("2")


@pytest.mark.parametrize(
    "history",
    [
        [trade(), trade("SELL", "11", day=1)],
        [trade("SELL")],
        [trade(), trade("SELL", symbol="VALE3", day=1)],
        [trade(), trade("SELL", portfolio=2, day=1)],
        [trade(), trade("SELL", day=1), trade("SELL", "1", day=2)],
    ],
)
def test_insufficient_position_is_domain_error(history) -> None:
    with pytest.raises(InsufficientPositionError, match="Insufficient position"):
        rebuild_positions(history)


def test_repurchase_resets_average_and_retains_cumulative_result() -> None:
    result = rebuild_positions(
        [
            trade(price="20"),
            trade("SELL", price="30", day=1),
            trade(quantity="5", price="50", day=2),
        ]
    )
    position = result.positions[0]
    assert (
        position.quantity,
        position.average_cost,
        position.cost_basis,
        position.realized_profit_loss,
    ) == (D("5"), D("50"), D("250"), D("100"))
    assert result.closed_positions == ()


def test_portfolio_and_asset_isolation_and_output_order() -> None:
    history = [
        trade(symbol="VALE3", price="20"),
        trade(portfolio=2, price="40"),
        trade(symbol=" petr4 "),
        trade("SELL", "2", "35", day=1),
    ]
    positions = rebuild_positions(history).positions
    assert [
        (p.portfolio_id, p.asset.symbol, p.quantity, p.cost_basis) for p in positions
    ] == [
        (1, "PETR4", D("8"), D("240")),
        (1, "VALE3", D("10"), D("200")),
        (2, "PETR4", D("10"), D("400")),
    ]


def test_out_of_order_history_is_replayed_from_scratch() -> None:
    history = two_buys() + [trade("SELL", "5", "42", "1", day=2)]
    expected = rebuild_positions(history)
    for shuffled in permutations(history):
        assert rebuild_positions(iter(shuffled)) == expected
    assert history[0].quantity == D("10")


def test_equal_timestamps_sort_by_available_ids() -> None:
    history = [
        trade(identity=1),
        trade("SELL", "5", "40", identity=2),
        trade(price="50", identity=3),
    ]
    expected = rebuild_positions(history)
    for shuffled in permutations(history):
        assert rebuild_positions(shuffled) == expected
    assert expected.positions[0].average_cost == D("43." + "3" * 48)


@pytest.mark.parametrize("identity", [None, 1])
def test_missing_ids_and_complete_ties_preserve_input_order(identity) -> None:
    buy = trade(identity=identity)
    sell = trade("SELL", identity=identity)
    assert rebuild_positions([buy, sell]).positions == ()
    with pytest.raises(InsufficientPositionError):
        rebuild_positions([sell, buy])


def test_mixed_ids_known_first_then_missing_in_input_order() -> None:
    buy = trade(identity=5)
    sell = trade("SELL", "5")
    rebuy = trade(quantity="5", price="50")
    result = rebuild_positions([sell, buy, rebuy])
    assert result.positions[0].average_cost == D("40")


def test_sell_fees_reduce_realized_profit_without_changing_average() -> None:
    no_fee = rebuild_positions(
        two_buys() + [trade("SELL", "5", "42", day=2)]
    ).positions[0]
    fee = rebuild_positions(
        two_buys() + [trade("SELL", "5", "42", "10", day=2)]
    ).positions[0]
    assert fee.average_cost == no_fee.average_cost == D("35.2")
    assert fee.cost_basis == no_fee.cost_basis == D("528")
    assert no_fee.realized_profit_loss - fee.realized_profit_loss == D("10")


def test_empty_history() -> None:
    assert rebuild_positions(iter(())).positions == ()
    assert rebuild_positions([]).closed_positions == ()


def test_context_is_predictable_and_global_context_is_unchanged() -> None:
    history = [trade(quantity="3", price="1", fees="1")]
    expected = rebuild_positions(history)
    assert expected.positions[0].average_cost == D("1." + "3" * 49)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        context.clear_flags()
        assert rebuild_positions(history) == expected
        assert getcontext().prec == 6
        assert getcontext().rounding == ROUND_DOWN
        assert getcontext().traps[Inexact]
        assert not any(context.flags.values())


def test_high_precision_inputs_are_not_rounded_to_cents_or_50_digits() -> None:
    price = "1." + "1234567890" * 6
    position = rebuild_positions([trade(quantity="1", price=price)]).positions[0]
    assert position.cost_basis == position.average_cost == D(price)


@pytest.mark.parametrize("quantity", ["0.001", "0.5", "1.25", "10.333", "3"])
@pytest.mark.parametrize("price", ["0.0001", "1", "30.123456"])
def test_invariants_after_each_valid_prefix(quantity, price) -> None:
    history = [
        trade(quantity=quantity, price=price, fees="0.01"),
        trade(quantity=quantity, price="50", day=1),
        trade("SELL", quantity, "20", "0.03", day=2),
        trade("SELL", quantity, "40", day=3),
        trade(quantity=quantity, price="10", day=4),
    ]
    for length in range(1, len(history) + 1):
        result = rebuild_positions(history[:length])
        for position in result.positions + result.closed_positions:
            assert position.quantity >= 0 and position.cost_basis >= 0
            if position.quantity:
                assert position.average_cost > 0
            else:
                assert position.average_cost == position.cost_basis == 0


def test_result_and_snapshots_are_immutable() -> None:
    result = rebuild_positions([trade()])
    assert isinstance(result.positions, tuple)
    with pytest.raises(FrozenInstanceError):
        result.positions = ()
    with pytest.raises(FrozenInstanceError):
        result.positions[0].cost_basis = D("0")


def test_aware_datetimes_are_ordered_as_utc_instants() -> None:
    buy = replace(trade(), occurred_at=START.replace(tzinfo=timezone.utc))
    sell = replace(
        trade("SELL"),
        occurred_at=(START + timedelta(hours=1)).replace(
            tzinfo=timezone(timedelta(hours=1))
        ),
    )
    assert rebuild_positions([buy, sell]).positions == ()
    with pytest.raises(InsufficientPositionError):
        rebuild_positions([sell, buy])


def test_mixed_naive_and_aware_dates_fail_explicitly() -> None:
    with pytest.raises(DomainValidationError, match="naive and aware"):
        rebuild_positions(
            [trade(), replace(trade(), occurred_at=START.replace(tzinfo=timezone.utc))]
        )


def test_invalid_history_fails_with_domain_error() -> None:
    with pytest.raises(DomainValidationError, match="Transaction"):
        rebuild_positions(["BUY"])


def test_unrelated_portfolios_and_assets_do_not_change_decimal_precision() -> None:
    buy = trade(quantity="3", price="1", fees="1")
    expected = rebuild_positions([buy]).positions[0]
    unrelated = [
        trade(quantity="1", price="1." + "1" * 100, symbol="VALE3"),
        trade(quantity="1", price="1." + "2" * 120, portfolio=2),
    ]
    assert rebuild_positions([buy, *unrelated]).positions[0] == expected
