from decimal import Decimal
from threading import get_ident

import pytest
from PySide6.QtCore import QCoreApplication, QDate, QDateTime, Qt, QTime, QTimer
from PySide6.QtWidgets import QPushButton
from test_application_and_integration import trade

from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
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
from nexo.ui.dialogs.forms import TransactionDialog
from nexo.ui.pages.assets_page import AssetsPage
from nexo.ui.windows.main_window import MainWindow
from nexo.ui.workers import TaskRunner


@pytest.fixture
def market_window(qtbot, tmp_path, provider):
    engine = create_database_engine(tmp_path / "market-ui.db")
    initialize_database(engine)
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    transactions = SqlAlchemyTransactionRepository(factory)
    first = portfolios.add(Portfolio("First")).id
    second = portfolios.add(Portfolio("Second")).id
    register = RegisterTransaction(transactions)
    register.execute(trade(first))
    positions = LoadPortfolioPositions(transactions)
    window = MainWindow(
        CreatePortfolio(portfolios),
        ListPortfolios(portfolios),
        register,
        ListTransactions(transactions),
        positions,
        load_valuation=LoadPortfolioValuation(positions, provider),
        search_assets=SearchAssets(provider),
        get_quote=GetAssetQuote(provider),
        get_history=GetAssetHistory(provider),
    )
    qtbot.addWidget(window)
    try:
        yield window, first, second, transactions
    finally:
        provider.release.set()
        if window.active_dialog is not None:
            window.active_dialog.close()
        window.close()
        window.wait_for_market()
        engine.dispose()


def test_real_metrics_and_rows_are_shared_by_overview_and_portfolios(
    market_window, qtbot
):
    window, first, _, _ = market_window
    window._select_portfolio(first)
    qtbot.waitUntil(
        lambda: (
            window.overview_page.metrics["market"].value_label.text() == "R$ 400,00"
        ),
        timeout=10000,
    )
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 300,00"
    assert window.overview_page.metrics["unrealized"].value_label.text() == "R$ 100,00"
    assert window.overview_page.metrics["return"].value_label.text() == "33,33%"
    for table in (
        window.overview_page.positions_table,
        window.portfolios_page.positions_table,
    ):
        assert table.item(0, 5).text() == "R$ 40,00"
        assert table.item(0, 6).text() == "R$ 400,00"
        assert "fake" in table.item(0, 5).toolTip()
    assert "R$ 400,00" in window.portfolios_page.market_labels[first][0].text()
    assert "Consultado" in window.overview_page.market_feedback.text()
    chart = window.overview_page.valuation_chart
    assert chart is not None
    sets = chart.chart().series()[0].barSets()
    assert sets[0].at(0) == 300 and sets[1].at(0) == 400


def test_global_refresh_without_selection_finishes_with_selection_guidance(
    market_window, qtbot
):
    window, first, _, _ = market_window
    assert window.selected_portfolio_id is None
    window.market_refresh.click()
    qtbot.waitUntil(
        lambda: "Consulta de mercado concluída" in window.overview_page.market_feedback.text(),
        timeout=10000,
    )
    assert "Selecione uma carteira" in window.overview_page.market_feedback.text()
    assert "R$ 400,00" in window.portfolios_page.market_labels[first][0].text()
    assert window.selected_portfolio_id is None


@pytest.mark.parametrize("safe", [False, True])
def test_global_refresh_shows_safe_provider_errors_only(market_window, qtbot, monkeypatch, safe):
    window, _, _, _ = market_window
    error = MarketDataUnavailableError("Contador local inválido.") if safe else RuntimeError("private-internal-data")

    def fail(identities, *, explicit=False):
        raise error

    monkeypatch.setattr(window._load_valuation, "execute_many", fail)
    window.market_refresh.click()
    qtbot.waitUntil(
        lambda: "Mercado indisponível" in window.overview_page.market_feedback.text(),
        timeout=10000,
    )
    message = window.overview_page.market_feedback.text()
    assert ("Contador local inválido." in message) is safe
    assert "private-internal-data" not in message


def test_manual_refresh_replaces_quote_without_changing_cost(
    market_window, qtbot, provider
):
    window, first, _, _ = market_window
    window._select_portfolio(first)
    qtbot.waitUntil(
        lambda: (
            window.overview_page.metrics["market"].value_label.text() == "R$ 400,00"
        ),
        timeout=10000,
    )
    calls = len(provider.calls)
    window.show_page(0)
    assert len(provider.calls) == calls
    provider.price = Decimal(45)
    window.refresh_market()
    qtbot.waitUntil(
        lambda: (
            window.overview_page.metrics["market"].value_label.text() == "R$ 450,00"
        ),
        timeout=10000,
    )
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 300,00"

    provider.price = Decimal(50)
    refresh = next(
        button
        for button in window.portfolios_page.findChildren(QPushButton)
        if button.text() == "Atualizar"
    )
    refresh.click()
    qtbot.waitUntil(
        lambda: (
            window.overview_page.metrics["market"].value_label.text() == "R$ 500,00"
        ),
        timeout=10000,
    )
    assert "R$ 500,00" in window.portfolios_page.market_labels[first][0].text()


def test_timeout_keeps_local_ledger_and_allows_trade(market_window, qtbot, provider):
    window, first, _, transactions = market_window
    provider.error = MarketDataUnavailableError("Sem rede")
    window._select_portfolio(first)
    qtbot.waitUntil(
        lambda: "Sem rede" in window.overview_page.market_feedback.text(), timeout=10000
    )
    assert window.overview_page.metrics["market"].value_label.text() == "—"
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 300,00"
    window.open_dialog("transaction")
    dialog = window.active_dialog
    assert isinstance(dialog, TransactionDialog)
    dialog.asset_symbol.setText("VALE3")
    dialog.quantity.setText("2")
    dialog.unit_price.setText("20")
    dialog.fees.setText("0")
    dialog.occurred_at.setDateTime(QDateTime(QDate(2026, 1, 2), QTime(10, 0)))
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert window.active_dialog is None
    assert len(transactions.list_by_portfolio(first)) == 2
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 340,00"


def test_slow_request_does_not_block_gui_or_apply_after_portfolio_switch(
    market_window, qtbot, provider
):
    window, first, second, _ = market_window
    window.wait_for_market()
    provider.block_next = True
    window._select_portfolio(first)
    qtbot.waitUntil(provider.entered.is_set, timeout=10000)
    heartbeats = []
    QTimer.singleShot(0, lambda: heartbeats.append(get_ident()))
    qtbot.waitUntil(lambda: bool(heartbeats), timeout=10000)
    assert heartbeats == [get_ident()] and not provider.release.is_set()
    window._select_portfolio(second)
    qtbot.waitUntil(
        lambda: window.overview_page.metrics["market"].value_label.text() == "R$ 0,00",
        timeout=10000,
    )
    provider.release.set()
    window.wait_for_market()
    QCoreApplication.processEvents()
    assert window.selected_portfolio_id == second
    assert window.overview_page.positions_table.rowCount() == 0
    assert window.overview_page.metrics["market"].value_label.text() == "R$ 0,00"


def test_worker_runs_outside_gui_and_callback_runs_on_gui(qtbot):
    runner = TaskRunner()
    ui_thread = get_ident()
    results = []
    runner.submit(
        get_ident, lambda result, error: results.append((result, error, get_ident()))
    )
    qtbot.waitUntil(lambda: bool(results), timeout=10000)
    assert (
        results[0][0] != ui_thread
        and results[0][1] is None
        and results[0][2] == ui_thread
    )
    runner.wait()


def test_unexpected_worker_failure_does_not_disclose_exception(
    market_window, qtbot, provider
):
    window, first, _, _ = market_window
    provider.error = RuntimeError("SECRET PRIVATE RESPONSE")
    window._select_portfolio(first)
    qtbot.waitUntil(
        lambda: (
            "Dados locais preservados" in window.overview_page.market_feedback.text()
        ),
        timeout=10000,
    )
    assert "SECRET" not in window.overview_page.market_feedback.text()
    assert window.overview_page.metrics["cost"].value_label.text() == "R$ 300,00"


def test_asset_search_quote_and_real_timestamp_chart(qtbot, provider):
    page = AssetsPage(
        SearchAssets(provider), GetAssetQuote(provider), GetAssetHistory(provider)
    )
    qtbot.addWidget(page)
    try:
        page.search_input.setText(" PETR ")
        page.search()
        qtbot.waitUntil(lambda: page.table.rowCount() == 2, timeout=10000)
        page.table.selectRow(0)
        qtbot.waitUntil(
            lambda: page.quote is not None and page.chart is not None, timeout=10000
        )
        assert page.quote.asset.symbol == "PETR4"
        assert "BRL" in page.quote_label.text() and "2,5%" in page.quote_label.text()
        series = page.chart.chart().series()[0]
        assert series.count() == 2 and series.at(1).y() == 31.5
        assert series.at(0).x() == page.history.points[0].timestamp.timestamp() * 1000
        assert (
            "fake" in page.history_label.text() and "1mo" in page.history_label.text()
        )
        page.period.setCurrentIndex(1)
        qtbot.waitUntil(
            lambda: page.history is not None and page.history.period == "3mo",
            timeout=10000,
        )
        assert provider.searches == ["PETR"]
    finally:
        page.runner.stop()
        page.runner.wait()


def test_history_failure_removes_previous_chart_but_keeps_quote(qtbot, provider):
    page = AssetsPage(
        SearchAssets(provider), GetAssetQuote(provider), GetAssetHistory(provider)
    )
    qtbot.addWidget(page)
    try:
        page.search()
        qtbot.waitUntil(lambda: bool(page.results), timeout=10000)
        page.table.selectRow(0)
        qtbot.waitUntil(
            lambda: page.chart is not None and page.quote is not None, timeout=10000
        )
        provider.history_error = MarketDataUnavailableError("Sem histórico")
        page.refresh_history()
        assert page.chart is None
        qtbot.waitUntil(
            lambda: page.history_label.text() == "Sem histórico", timeout=10000
        )
        assert page.history is None and page.quote is not None
    finally:
        page.runner.stop()
        page.runner.wait()


def test_asset_search_failure_does_not_show_demo_rows(qtbot, provider):
    provider.error = MarketDataUnavailableError("Sem conexão")
    page = AssetsPage(
        SearchAssets(provider), GetAssetQuote(provider), GetAssetHistory(provider)
    )
    qtbot.addWidget(page)
    try:
        page.search()
        qtbot.waitUntil(lambda: page.feedback.text() == "Sem conexão", timeout=10000)
        assert page.table.rowCount() == 0 and page.chart is None and page.quote is None
    finally:
        page.runner.stop()
        page.runner.wait()


def test_foreign_quote_is_named_but_not_summed_in_brl(market_window, qtbot, provider):
    window, first, _, _ = market_window
    provider.currency = "USD"
    window._select_portfolio(first)
    qtbot.waitUntil(
        lambda: window.overview_page.positions_table.item(0, 5).text() == "USD 40",
        timeout=10000,
    )
    assert window.overview_page.metrics["market"].value_label.text() == "—"
    assert window.overview_page.positions_table.item(0, 6).text() == "USD 400"
    assert "moeda" in window.overview_page.market_feedback.text()


def test_stale_asset_quote_is_discarded_after_selection_changes(qtbot, provider):
    page = AssetsPage(
        SearchAssets(provider), GetAssetQuote(provider), GetAssetHistory(provider)
    )
    qtbot.addWidget(page)
    try:
        page.search()
        qtbot.waitUntil(lambda: bool(page.results), timeout=10000)
        provider.block_next = True
        page.table.selectRow(0)
        qtbot.waitUntil(provider.entered.is_set, timeout=10000)
        provider.price = Decimal(45)
        page.table.selectRow(1)
        qtbot.waitUntil(
            lambda: page.quote is not None and page.quote.asset.symbol == "VALE3",
            timeout=10000,
        )
        provider.release.set()
        page.runner.wait()
        QCoreApplication.processEvents()
        assert page.quote.asset.symbol == "VALE3" and page.quote.price == 45
        assert page.history.asset.symbol == "VALE3"
    finally:
        provider.release.set()
        page.runner.stop()
        page.runner.wait()


def test_empty_history_never_draws_fake_series(qtbot, provider):
    provider.empty_history = True
    page = AssetsPage(
        SearchAssets(provider), GetAssetQuote(provider), GetAssetHistory(provider)
    )
    qtbot.addWidget(page)
    try:
        page.search()
        qtbot.waitUntil(lambda: bool(page.results), timeout=10000)
        page.table.selectRow(0)
        qtbot.waitUntil(lambda: page.history is not None, timeout=10000)
        assert page.chart is None and "Nenhum ponto" in page.history_label.text()
    finally:
        page.runner.stop()
        page.runner.wait()
