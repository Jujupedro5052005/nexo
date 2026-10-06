from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from nexo.application.portfolio.financial_summary import (
    summarize_portfolio,
    transaction_amounts,
)
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.interfaces.transaction_repository import (
    TransactionRepository,
    TransactionRepositoryError,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions

START = datetime.fromisoformat("2026-01-01T10:00:00")


class MemoryLedger(TransactionRepository):
    def __init__(self):
        self.items = []
        self.add_calls = 0

    def add(self, transaction):
        self.add_calls += 1
        saved = replace(transaction, id=len(self.items) + 1)
        self.items.append(saved)
        return saved

    def list_by_portfolio(self, portfolio_id):
        return [t for t in self.items if t.portfolio_id == portfolio_id]


def trade(
    kind=TransactionType.BUY, quantity="10", *, hour=0, portfolio=1, symbol="PETR4"
):
    return Transaction(
        portfolio,
        Asset(symbol),
        kind,
        Decimal(quantity),
        Decimal(30),
        Decimal(0),
        START + timedelta(hours=hour),
    )


def test_register_buy_then_sell() -> None:
    ledger = MemoryLedger()
    register = RegisterTransaction(ledger)
    buy = register.execute(trade())
    sell = register.execute(trade(TransactionType.SELL, "5", hour=1))
    assert buy.id == 1 and sell.id == 2
    assert LoadPortfolioPositions(ledger).execute(1).positions[0].quantity == 5


@pytest.mark.parametrize(
    "history, candidate",
    [
        ([], trade(TransactionType.SELL)),
        ([trade()], trade(TransactionType.SELL, "11", hour=1)),
        ([trade()], trade(TransactionType.SELL, "1", hour=-1)),
        (
            [trade(), trade(TransactionType.SELL, hour=2)],
            trade(TransactionType.SELL, "1", hour=1),
        ),
        ([trade()], trade(TransactionType.SELL, "1", hour=1, portfolio=2)),
        ([trade()], trade(TransactionType.SELL, "1", hour=1, symbol="VALE3")),
    ],
)
def test_invalid_history_is_rejected_before_insert(history, candidate) -> None:
    ledger = MemoryLedger()
    register = RegisterTransaction(ledger)
    for item in history:
        register.execute(item)
    previous_calls = ledger.add_calls
    previous_history = list(ledger.items)
    with pytest.raises(InsufficientPositionError):
        register.execute(candidate)
    assert ledger.add_calls == previous_calls
    assert ledger.items == previous_history


def test_valid_retroactive_buy_replays_full_history() -> None:
    ledger = MemoryLedger()
    register = RegisterTransaction(ledger)
    register.execute(trade(hour=1))
    register.execute(trade(TransactionType.SELL, hour=2))
    register.execute(trade(quantity="5", hour=-1))
    assert LoadPortfolioPositions(ledger).execute(1).positions[0].quantity == 5


def test_same_timestamp_new_id_preserves_candidate_result() -> None:
    ledger = MemoryLedger()
    register = RegisterTransaction(ledger)
    register.execute(trade())
    candidate = trade(TransactionType.SELL, "5")
    expected = rebuild_positions([*ledger.items, candidate])
    register.execute(candidate)
    assert LoadPortfolioPositions(ledger).execute(1) == expected


def test_register_rejects_existing_identity() -> None:
    ledger = MemoryLedger()
    with pytest.raises(DomainValidationError):
        RegisterTransaction(ledger).execute(replace(trade(), id=1))
    assert ledger.add_calls == 0


@pytest.mark.parametrize("method", ["add", "list_by_portfolio"])
def test_register_propagates_storage_failure_without_false_success(
    monkeypatch, method
) -> None:
    ledger = MemoryLedger()

    def fail(_item):
        raise TransactionRepositoryError("Failure")

    monkeypatch.setattr(ledger, method, fail)
    with pytest.raises(TransactionRepositoryError):
        RegisterTransaction(ledger).execute(trade())
    assert ledger.items == []


def test_list_transactions_orders_and_isolates_entities() -> None:
    ledger = MemoryLedger()
    late = ledger.add(trade(hour=2))
    ledger.add(trade(portfolio=2))
    early = ledger.add(trade())
    assert [t.id for t in ListTransactions(ledger).execute(1)] == [early.id, late.id]
    assert all(isinstance(t, Transaction) for t in ListTransactions(ledger).execute(1))


@pytest.mark.parametrize("identity", [0, -1, True])
def test_invalid_portfolio_id_in_reads(identity) -> None:
    ledger = MemoryLedger()
    with pytest.raises(DomainValidationError):
        ListTransactions(ledger).execute(identity)
    with pytest.raises(DomainValidationError):
        LoadPortfolioPositions(ledger).execute(identity)


def test_load_positions_empty_and_closed_results() -> None:
    ledger = MemoryLedger()
    load = LoadPortfolioPositions(ledger)
    assert load.execute(1).positions == ()
    register = RegisterTransaction(ledger)
    register.execute(trade())
    register.execute(
        replace(trade(TransactionType.SELL, hour=1), unit_price=Decimal(40))
    )
    result = load.execute(1)
    assert result.positions == ()
    assert result.closed_positions[0].realized_profit_loss == 100
    summary = load.summary(1)
    assert summary.positions_count == 0 and summary.transactions_count == 2
    assert summary.cost_basis == 0 and summary.realized_profit_loss == 100


def test_summary_and_amounts_preserve_high_precision() -> None:
    price = Decimal("1.123456789012345678901234567890123456789")
    item = replace(trade(quantity="1"), unit_price=price)
    result = rebuild_positions([item])
    assert summarize_portfolio([item], result).cost_basis == price
    gross, total = transaction_amounts(item)
    assert gross == total == price
    sale = replace(item, transaction_type=TransactionType.SELL, fees=Decimal("0.1"))
    assert transaction_amounts(sale)[1] == Decimal(
        "1.023456789012345678901234567890123456789"
    )


@pytest.mark.parametrize(
    "kind, expected", [(TransactionType.BUY, "302"), (TransactionType.SELL, "298")]
)
def test_display_amounts_share_transaction_fee_policy(kind, expected) -> None:
    item = replace(trade(kind), fees=Decimal(2))
    assert item.amounts() == (Decimal(300), Decimal(expected))
    assert transaction_amounts(item) == item.amounts()
