from dataclasses import replace
from decimal import Decimal

import pytest
from PySide6.QtCore import QDate, QDateTime, Qt, QTime
from PySide6.QtWidgets import QLabel

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from nexo.main import create_application
from nexo.ui.dialogs.forms import PortfolioDialog, TransactionDialog
from nexo.ui.windows.main_window import MainWindow


def open_window(path, qtbot):
    create_application()
    engine = create_database_engine(path)
    initialize_database(engine)
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    transactions = SqlAlchemyTransactionRepository(factory)
    window = MainWindow(
        CreatePortfolio(portfolios),
        ListPortfolios(portfolios),
        RegisterTransaction(transactions),
        ListTransactions(transactions),
        LoadPortfolioPositions(transactions),
    )
    qtbot.addWidget(window)
    window.show()
    return window, engine, portfolios, transactions


@pytest.fixture
def financial_window(tmp_path, qtbot):
    window, engine, portfolios, transactions = open_window(
        tmp_path / "ui-ledger.db", qtbot
    )
    first = portfolios.add(Portfolio("Igual"))
    second = portfolios.add(Portfolio("Igual"))
    window.show_page(1)
    window.portfolios_page.reload()
    try:
        yield window, engine, transactions, first.id, second.id
    finally:
        if window.active_dialog is not None:
            window.active_dialog.close()
        window.close()
        engine.dispose()


def select(window, qtbot, identity):
    window.show_page(1)
    qtbot.mouseClick(
        window.portfolios_page.selection_buttons[identity], Qt.MouseButton.LeftButton
    )


def open_trade(
    window, *, kind="BUY", symbol="PETR4", quantity="10", price="30", fees="2", hour=10
):
    window.open_dialog("transaction")
    dialog = window.active_dialog
    assert isinstance(dialog, TransactionDialog)
    dialog.transaction_type.setCurrentIndex(0 if kind == "BUY" else 1)
    dialog.asset_symbol.setText(symbol)
    dialog.quantity.setText(quantity)
    dialog.unit_price.setText(price)
    dialog.fees.setText(fees)
    dialog.occurred_at.setDateTime(QDateTime(QDate(2026, 1, 1), QTime(hour, 0)))
    return dialog


def save_trade(window, qtbot, **fields):
    dialog = open_trade(window, **fields)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert window.active_dialog is None


def test_no_selected_portfolio_has_no_mock_finances_and_cannot_save(
    financial_window,
) -> None:
    window, _, repository, _, _ = financial_window
    window.show_page(3)
    assert window.transactions_page.table.rowCount() == 0
    assert not window.transactions_page.create_button.isEnabled()
    window.open_dialog("transaction")
    dialog = window.active_dialog
    assert isinstance(dialog, TransactionDialog)
    assert not dialog.save_button.isEnabled()
    assert "Selecione uma carteira" in dialog.feedback.text()
    assert window.overview_page.metrics["cost"].value_label.text() == "—"
    assert repository.list_by_portfolio(1) == []


def test_empty_selected_portfolio_has_real_empty_state(financial_window, qtbot) -> None:
    window, _, _, first, _ = financial_window
    select(window, qtbot, first)
    window.show_page(3)
    assert window.transactions_page.empty_label.isVisible()
    assert "Nenhuma movimentação" in window.transactions_page.empty_label.text()
    assert window.portfolios_page.positions_table.rowCount() == 0
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 0,00"
    assert window.overview_page.metrics["transactions"].value_label.text() == "0"


def test_buy_immediately_updates_history_positions_cards_and_overview(
    financial_window, qtbot
) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)
    assert len(repository.list_by_portfolio(first)) == 1
    assert window.transactions_page.table.rowCount() == 1
    assert window.transactions_page.table.item(0, 1).text() == "BUY"
    assert window.portfolios_page.positions_table.item(0, 0).text() == "PETR4"
    assert window.portfolios_page.positions_table.item(0, 1).text() == "10"
    assert window.portfolios_page.positions_table.item(0, 2).text() == "R$ 30,20"
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 302,00"
    labels = [label.text() for label in window.portfolios_page.findChildren(QLabel)]
    assert "Capital alocado a custo: R$ 302,00" in labels
    assert not any("demonstrativos" in label for label in labels)


def test_sell_updates_realized_result_and_remaining_cost(
    financial_window, qtbot
) -> None:
    window, _, _, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)
    save_trade(window, qtbot, price="40", hour=11)
    save_trade(window, qtbot, kind="SELL", quantity="5", price="42", fees="1", hour=12)
    table = window.portfolios_page.positions_table
    assert [table.item(0, c).text() for c in range(5)] == [
        "PETR4",
        "15",
        "R$ 35,20",
        "R$ 528,00",
        "R$ 33,00",
    ]
    assert window.transactions_page.table.rowCount() == 3
    assert window.transactions_page.table.item(2, 7).text() == "R$ 209,00"
    assert window.overview_page.metrics["realized"].value_label.text() == "R$ 33,00"


def test_invalid_sale_keeps_dialog_open_and_does_not_persist(
    financial_window, qtbot
) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot, quantity="5", fees="0")
    dialog = open_trade(window, kind="SELL", quantity="8", fees="0", hour=11)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible()
    assert dialog.feedback.isVisible()
    assert "5 PETR4" in dialog.feedback.text() and "vender 8" in dialog.feedback.text()
    assert len(repository.list_by_portfolio(first)) == 1
    assert window.transactions_page.table.rowCount() == 1
    assert dialog.save_button.isEnabled()


def test_ui_retroactive_sale_is_rejected(financial_window, qtbot) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)
    dialog = open_trade(window, kind="SELL", quantity="1", hour=9)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert "0 PETR4" in dialog.feedback.text()
    assert len(repository.list_by_portfolio(first)) == 1


def test_same_names_switch_by_id_without_leaking_data(financial_window, qtbot) -> None:
    window, _, _, first, second = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)
    select(window, qtbot, second)
    assert window.transactions_page.table.rowCount() == 0
    assert window.portfolios_page.positions_table.rowCount() == 0
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 0,00"
    save_trade(window, qtbot, symbol="VALE3", quantity="2", price="50", fees="0")
    assert window.portfolios_page.positions_table.item(0, 0).text() == "VALE3"
    select(window, qtbot, first)
    assert window.portfolios_page.positions_table.item(0, 0).text() == "PETR4"
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 302,00"


def test_filters_type_asset_search_and_period(financial_window, qtbot) -> None:
    window, _, _, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)
    save_trade(window, qtbot, symbol="VALE3", fees="0", hour=11)
    save_trade(window, qtbot, kind="SELL", quantity="1", fees="0", hour=12)
    page = window.transactions_page
    page.type_filter.setCurrentIndex(2)
    assert page.table.rowCount() == 1 and page.table.item(0, 1).text() == "SELL"
    page.type_filter.setCurrentIndex(0)
    page.asset_filter.setCurrentText("VALE3")
    assert page.table.rowCount() == 1 and page.table.item(0, 2).text() == "VALE3"
    page.asset_filter.setCurrentIndex(0)
    page.search.setText(" petr ")
    assert page.table.rowCount() == 2
    page.search.clear()
    old = [
        replace(t, occurred_at=t.occurred_at.replace(year=2000))
        for t in page._transactions
    ]
    page.set_data(first, old)
    page.period_filter.setCurrentText("Hoje")
    assert page.table.rowCount() == 0
    page.period_filter.setCurrentText("Máximo")
    assert page.table.rowCount() == 3


def test_decimal_form_accepts_dot_and_comma(financial_window, qtbot) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot, quantity="1.25", price="10,50", fees="0,25")
    item = repository.list_by_portfolio(first)[0]
    assert item.quantity == Decimal("1.25")
    assert item.unit_price == Decimal("10.50") and item.fees == Decimal("0.25")


@pytest.mark.parametrize(
    "field, value", [("quantity", "NaN"), ("unit_price", "-1"), ("fees", "Infinity")]
)
def test_invalid_parser_input_keeps_form_and_ledger_unchanged(
    financial_window, qtbot, field, value
) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)
    dialog = open_trade(window)
    getattr(dialog, field).setText(value)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible() and dialog.feedback.isVisible()
    assert repository.list_by_portfolio(first) == []


def test_storage_failure_hides_technical_details_and_retains_input(
    financial_window, qtbot, monkeypatch
) -> None:
    window, _, repository, first, _ = financial_window
    select(window, qtbot, first)

    def fail(_transaction):
        raise TransactionRepositoryError("IntegrityError SECRET SQL traceback")

    monkeypatch.setattr(repository, "add", fail)
    dialog = open_trade(window)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible() and dialog.save_button.isEnabled()
    assert dialog.quantity.text() == "10"
    assert "SECRET" not in dialog.feedback.text()
    assert "IntegrityError" not in dialog.feedback.text()
    assert repository.list_by_portfolio(first) == []


def test_failed_switch_clears_selected_financial_data(
    financial_window, qtbot, monkeypatch
) -> None:
    window, _, repository, first, second = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot)

    def fail(_identity):
        raise TransactionRepositoryError("SECRET")

    monkeypatch.setattr(repository, "list_by_portfolio", fail)
    select(window, qtbot, second)
    assert window.selected_portfolio_id == second
    assert window.transactions_page.table.rowCount() == 0
    assert window.portfolios_page.positions_table.rowCount() == 0
    assert window.overview_page.metrics["cost"].value_label.text() == "—"
    assert "SECRET" not in window.overview_page.context_label.text()


def test_closure_preserves_realized_summary_without_open_position(
    financial_window, qtbot
) -> None:
    window, _, _, first, _ = financial_window
    select(window, qtbot, first)
    save_trade(window, qtbot, price="20", fees="0")
    save_trade(window, qtbot, kind="SELL", price="30", fees="0", hour=11)
    assert window.portfolios_page.positions_table.rowCount() == 0
    assert window.overview_page.metrics["realized"].value_label.text() == "R$ 100,00"
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 0,00"


def test_full_ui_flow_creates_portfolio_registers_and_reopens(tmp_path, qtbot) -> None:
    path = tmp_path / "representative.db"
    window, engine, _, repository = open_window(path, qtbot)
    try:
        window.open_dialog("portfolio")
        dialog = window.active_dialog
        assert isinstance(dialog, PortfolioDialog)
        dialog.name_field.setText("Teste")
        qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        identity = window.selected_portfolio_id
        save_trade(window, qtbot)
        save_trade(window, qtbot, price="40", hour=11)
        save_trade(
            window, qtbot, kind="SELL", quantity="5", price="42", fees="1", hour=12
        )
        expected = window._load_positions.execute(identity)
        expected_history = repository.list_by_portfolio(identity)
        window.show_page(3)
        window.grab().save(str(tmp_path / "financial-window.png"))
        print(f"UI screenshot: {tmp_path / 'financial-window.png'}")
    finally:
        window.close()
        engine.dispose()
    reopened, engine, _, repository = open_window(path, qtbot)
    try:
        assert reopened.selected_portfolio_id is None
        select(reopened, qtbot, identity)
        assert repository.list_by_portfolio(identity) == expected_history
        assert reopened._load_positions.execute(identity) == expected
        p = expected.positions[0]
        assert (
            p.quantity,
            p.average_cost,
            p.cost_basis,
            p.realized_profit_loss,
        ) == tuple(map(Decimal, ("15", "35.2", "528", "33")))
        assert reopened.transactions_page.table.rowCount() == 3
        invalid = open_trade(
            reopened, kind="SELL", quantity="16", price="50", fees="0", hour=13
        )
        qtbot.mouseClick(invalid.save_button, Qt.MouseButton.LeftButton)
        assert invalid.feedback.isVisible()
        assert len(repository.list_by_portfolio(identity)) == 3
        invalid.close()
    finally:
        reopened.close()
        engine.dispose()
