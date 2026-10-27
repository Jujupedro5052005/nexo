from datetime import date, datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
)

from nexo.application.financial_planning.manage_finances import ManageFinances
from nexo.application.local_data import LocalDataError, ManageLocalData
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.export_report import ExportReport
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.calculations.valuation.trade import quantity_for_total, trade_total
from nexo.domain.models.market_data import Quote
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal, PriceAlert
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.infrastructure.database.local_data import SqliteLocalDataStorage
from nexo.infrastructure.database.repositories.personal_finance import (
    SqlPersonalFinanceRepository,
)
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
from nexo.infrastructure.persistence.report_writer import CsvReportWriter
from nexo.ui import preferences as prefs
from nexo.ui.dialogs.transaction_dialog import TransactionDialog
from nexo.ui.windows.main_window import MainWindow


@pytest.fixture
def isolated_preferences(monkeypatch, tmp_path, qapp):
    original_style = qapp.styleSheet()
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(prefs, "preferences", lambda: settings)
    monkeypatch.setattr("nexo.ui.windows.main_window.preferences", lambda: settings)
    yield settings
    qapp.setStyleSheet(original_style)


@pytest.fixture
def closing_window(qtbot, tmp_path, isolated_preferences):
    engine = create_database_engine(tmp_path / "closing.db")
    initialize_database(engine)
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    trades = SqlAlchemyTransactionRepository(factory)
    finances = ManageFinances(SqlPersonalFinanceRepository(factory), None)
    identity = portfolios.add(Portfolio("Fechamento")).id
    calls = []

    def quote(asset, **kwargs):
        calls.append((asset.symbol, kwargs))
        return Quote(
            asset,
            D(30),
            "BRL",
            asset.symbol,
            datetime.now(timezone.utc),
            source="fixture",
        )

    storage = SqliteLocalDataStorage(engine)
    window = MainWindow(
        CreatePortfolio(portfolios),
        ListPortfolios(portfolios),
        RegisterTransaction(trades),
        ListTransactions(trades),
        LoadPortfolioPositions(trades),
        get_quote=SimpleNamespace(execute=quote, get_integration_status=lambda: None),
        finances=finances,
        local_data=ManageLocalData(storage),
        export_report=ExportReport(
            ListTransactions(trades),
            LoadPortfolioPositions(trades),
            finances,
            CsvReportWriter(),
            events=trades,
        ),
    )
    qtbot.addWidget(window)
    window.show()
    window._select_portfolio(identity)
    yield window, trades, portfolios, finances, storage, calls
    if window.active_dialog is not None:
        window.active_dialog.close()
    window.close()
    window.wait_for_market()
    storage.engine.dispose()


@pytest.mark.parametrize(
    "budget,price", [("100", "3"), ("0.01", "1234567"), ("5000.50", "32.71")]
)
def test_budget_never_exceeded(budget, price):
    quantity = quantity_for_total(D(budget), D(price))
    assert trade_total(quantity, D(price)) <= D(budget)
    assert D(budget) - trade_total(quantity, D(price)) < D(price) * D(".00000001")


def test_auto_quote_sync_manual_and_persisted_buy_sell(closing_window, qtbot):
    window, trades, _, _, _, calls = closing_window
    identity = window.selected_portfolio_id
    window.open_dialog("transaction")
    dialog = window.active_dialog
    dialog.asset_symbol.setText("PETR4")
    dialog.total_amount.setText("100")
    qtbot.waitUntil(lambda: dialog.unit_price.text() == "30", timeout=3000)
    assert len(calls) == 1
    assert dialog.quantity.text() == "3,33333333"
    assert dialog.unit_price.isReadOnly()
    dialog.manual_price.setChecked(True)
    dialog.unit_price.setText("25")
    assert dialog.quantity.text() == "4"
    dialog.quote_button.click()
    qtbot.waitUntil(lambda: dialog.unit_price.text() == "30", timeout=3000)
    assert calls[-1][1]["refresh"] is True
    assert not dialog.manual_price.isChecked()
    dialog.manual_price.setChecked(True)
    dialog.unit_price.setText("25")
    dialog.quantity.setText("10")
    assert dialog.total_amount.text() == "250"
    assert dialog._transaction().fees == 0
    dialog.save_button.click()
    assert len(trades.list_by_portfolio(identity)) == 1
    assert window.transactions_page.table.rowCount() == 1
    window.open_dialog("transaction")
    sale = window.active_dialog
    sale.transaction_type.setCurrentIndex(1)
    sale.asset_symbol.setText("PETR4")
    sale.manual_price.setChecked(True)
    sale.unit_price.setText("30")
    sale.quantity.setText("11")
    sale.save_button.click()
    assert sale.feedback.isVisible()
    assert len(trades.list_by_portfolio(identity)) == 1
    sale.quantity.setText("5")
    sale.save_button.click()
    assert len(trades.list_by_portfolio(identity)) == 2
    assert window._load_positions.execute(identity).positions[0].quantity == 5
    reopened = create_database_engine(Path(window._local_data.location))
    try:
        repository = SqlAlchemyTransactionRepository(create_session_factory(reopened))
        assert repository.list_by_portfolio(identity) == trades.list_by_portfolio(
            identity
        )
    finally:
        reopened.dispose()


@pytest.mark.parametrize("failure", ["offline", "foreign", "wrong_asset"])
def test_quote_failure_allows_manual_entry(qtbot, failure):
    from nexo.domain.models.asset import Asset

    def quote(asset, **_kwargs):
        if failure == "offline":
            raise RuntimeError("secret diagnostic")
        return Quote(
            Asset("VALE3") if failure == "wrong_asset" else asset,
            D(20),
            "USD" if failure == "foreign" else "BRL",
            "Fixture",
            datetime.now(timezone.utc),
        )

    dialog = TransactionDialog(get_quote=SimpleNamespace(execute=quote), portfolio_id=1)
    qtbot.addWidget(dialog)
    dialog.asset_symbol.setText("PETR4")
    dialog.quantity.setText("10")
    qtbot.waitUntil(
        lambda: "indisponível" in dialog.reference_label.text(), timeout=3000
    )
    assert not dialog.unit_price.text()
    assert "secret" not in dialog.reference_label.text()
    dialog.manual_price.setChecked(True)
    dialog.unit_price.setText("12,50")
    assert dialog.total_amount.text() == "125"
    dialog.close()
    dialog.runner.wait()


def test_slow_quote_cannot_replace_manual_or_new_asset(qtbot):
    started, release = Event(), Event()

    def quote(asset, **_kwargs):
        started.set()
        release.wait(3)
        return Quote(asset, D(99), "BRL", "Fixture", datetime.now(timezone.utc))

    dialog = TransactionDialog(get_quote=SimpleNamespace(execute=quote), portfolio_id=1)
    qtbot.addWidget(dialog)
    dialog.asset_symbol.setText("PETR4")
    dialog.load_reference()
    qtbot.waitUntil(started.is_set)
    dialog.manual_price.setChecked(True)
    dialog.asset_symbol.setText("VALE3")
    dialog.unit_price.setText("45")
    release.set()
    dialog.runner.wait()
    qtbot.wait(30)
    assert dialog.unit_price.text() == "45"
    assert "manual" in dialog.reference_label.text().lower()
    dialog.close()


def test_clear_invalid_input_clears_derived_values(qtbot):
    dialog = TransactionDialog(portfolio_id=1)
    qtbot.addWidget(dialog)
    dialog.unit_price.setText("20")
    dialog.quantity.setText("2")
    assert dialog.total_amount.text() == "40"
    dialog.total_amount.clear()
    assert not dialog.quantity.text()
    dialog.total_amount.setText("100")
    dialog.unit_price.clear()
    assert not dialog.quantity.text()
    dialog.unit_price.setText("25")
    assert dialog.quantity.text() == "4"
    dialog.close()


def test_backup_reset_cancel_confirm_and_reuse(
    closing_window, qtbot, tmp_path, monkeypatch
):
    window, trades, portfolios, finances, storage, _ = closing_window
    with storage.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA journal_mode=WAL").scalar_one() == "wal"
    trades.add_event(
        PortfolioEvent(
            window.selected_portfolio_id,
            PortfolioEventType.OPENING,
            datetime(2026, 1, 1),  # noqa: DTZ001 -- UI wall-clock convention
            D(1000),
        )
    )
    window.open_dialog("transaction")
    dialog = window.active_dialog
    dialog.asset_symbol.setText("PETR4")
    dialog.manual_price.setChecked(True)
    dialog.unit_price.setText("25")
    dialog.quantity.setText("4")
    dialog.save_button.click()
    identity = window.selected_portfolio_id
    finances.save_budget(BudgetEntry("Salário", D(5000), "income", date(2026, 10, 27)))
    finances.save_goal(FinancialGoal("Reserva", D(1000), D(50), date(2026, 10, 27)))
    finances.save_alert(PriceAlert("PETR4", D(25), "below"))
    panel = window.settings_page.local_data_panel
    destination = tmp_path / "export.db"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(destination), "")
    )
    panel.export_button.click()
    qtbot.waitUntil(lambda: not panel.busy)
    assert destination.exists()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No
    )
    panel.clear_button.click()
    assert len(portfolios.list_all()) == 1
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    panel.clear_button.click()
    qtbot.waitUntil(lambda: not panel.busy, timeout=5000)
    assert not portfolios.list_all()
    with storage.engine.connect() as connection:
        assert (
            connection.exec_driver_sql("SELECT COUNT(*) FROM transactions").scalar_one()
            == 0
        )
        assert (
            connection.exec_driver_sql(
                "SELECT COUNT(*) FROM portfolio_events"
            ).scalar_one()
            == 0
        )
    assert (
        not finances.goals() and not finances.budget_entries() and not finances.alerts()
    )
    assert window.selected_portfolio_id is None
    assert not window.portfolios_page.portfolio_ids
    assert window.transactions_page.table.rowCount() == 0
    backups = list(tmp_path.glob("closing_backup_*.db"))
    assert len(backups) == 1
    backup_engine = create_database_engine(backups[0])
    try:
        factory = create_session_factory(backup_engine)
        assert len(SqlAlchemyPortfolioRepository(factory).list_all()) == 1
        assert len(SqlPersonalFinanceRepository(factory).goals()) == 1
        restored = SqlAlchemyTransactionRepository(factory)
        assert len(restored.list_by_portfolio(identity)) == 1
        assert len(restored.list_events(identity)) == 1
    finally:
        backup_engine.dispose()
    window.open_dialog("portfolio")
    window.active_dialog.name_field.setText("Nova")
    window.active_dialog.save_button.click()
    assert window.selected_portfolio_id is not None
    assert len(portfolios.list_all()) == 1
    assert storage.path.exists()


def test_backup_failure_prevents_reset_and_self_overwrite(closing_window, monkeypatch):
    _, _, portfolios, _, storage, _ = closing_window
    with pytest.raises(LocalDataError):
        storage.backup(storage.path)

    def fail(_path):
        raise LocalDataError("Fixture failure")

    monkeypatch.setattr(storage, "backup", fail)
    with pytest.raises(LocalDataError):
        storage.clear()
    assert len(portfolios.list_all()) == 1


def test_reset_rolls_back_all_tables_on_sql_failure(closing_window):
    _, _, portfolios, finances, storage, _ = closing_window
    finances.save_goal(FinancialGoal("Reserva", D(1000), D(50), date(2026, 10, 27)))
    with storage.engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TRIGGER protect_portfolios BEFORE DELETE ON portfolios BEGIN SELECT RAISE(ABORT, 'fixture'); END"
        )
    with pytest.raises(LocalDataError):
        storage.clear()
    assert len(portfolios.list_all()) == 1
    assert len(finances.goals()) == 1


def test_profile_themes_period_notifications_and_exit(
    closing_window, monkeypatch, isolated_preferences
):
    window, *_ = closing_window
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("João", True))
    window._edit_profile()
    assert window.profile_label.text() == "João"
    assert isolated_preferences.value("profile/name") == "João"
    for mode in ("light", "system", "dark"):
        window.settings_page.findChild(QRadioButton, f"theme_{mode}").setChecked(True)
        assert prefs.theme_choice() == mode
    window.findChild(
        QComboBox,
        "period_selector",
    ).setCurrentText("7 dias")
    assert window.page_stack.currentIndex() == 3
    assert window.transactions_page.period_filter.currentText() == "7 dias"
    window.open_dialog("notifications")
    assert window.page_stack.currentIndex() == 6
    next(b for b in window.findChildren(QPushButton) if b.text() == "Sair").click()
    assert not window.isVisible()


def test_planning_goal_alert_buttons_and_all_reports(
    closing_window, monkeypatch, tmp_path
):
    window, _, _, finances, _, _ = closing_window
    for page, values in (
        (window.planning_page, ["Salário", "4000"]),
        (window.goals_page, ["Reserva", "12000", "1000"]),
        (window.alerts_page, ["PETR4", "30"]),
    ):
        page.add_button.click()
        editor = page.editor
        fields = [
            field
            for field in editor.findChildren(QLineEdit)
            if field.parent() is editor
        ]
        for field, value in zip(fields, values, strict=True):
            field.setText(value)
        editor.findChild(QDialogButtonBox).button(
            QDialogButtonBox.StandardButton.Save
        ).click()
        assert page.table.rowCount() == 1
    assert finances.budget_entries()[0].amount == 4000
    assert finances.goals()[0].current == 1000
    assert finances.alerts()[0].threshold == 30
    reports = window.reports_page
    for index in range(reports.kind.count()):
        reports.kind.setCurrentIndex(index)
        destination = tmp_path / f"{reports.kind.currentData()}.csv"
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *args, path=destination: (str(path), ""),
        )
        reports.generate.click()
        assert destination.read_text(encoding="utf-8-sig").strip()
        assert "Relatório salvo" in reports.feedback.text()


def test_visual_review(closing_window, qtbot, tmp_path):
    from PySide6.QtGui import QFontDatabase

    font = Path("C:/Windows/Fonts/segoeui.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font)) if font.exists() else -1
    window, *_ = closing_window
    for theme in ("dark", "light"):
        window.settings_page.findChild(QRadioButton, f"theme_{theme}").setChecked(True)
        window.show_page(9)
        qtbot.wait(20)
        assert window.grab().save(str(tmp_path / f"settings_{theme}.png"))
        window.open_dialog("transaction")
        dialog = window.active_dialog
        dialog.asset_symbol.setText("PETR4")
        dialog.manual_price.setChecked(True)
        dialog.unit_price.setText("32,71")
        dialog.total_amount.setText("1000")
        qtbot.wait(20)
        assert dialog.grab().save(str(tmp_path / f"transaction_{theme}.png"))
        dialog.close()
    print(f"Visual review: {tmp_path}")
    if font_id >= 0:
        QFontDatabase.removeApplicationFont(font_id)
