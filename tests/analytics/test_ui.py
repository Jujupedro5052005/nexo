from datetime import date
from decimal import Decimal
from threading import get_ident

import pytest
from analytics_helpers import analytics_trade
from PySide6.QtCore import QTimer

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import GetAssetHistory, GetAssetQuote
from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import AssetSearchResult
from nexo.ui.components.asset_analysis_panel import AssetAnalysisPanel
from nexo.ui.pages.analysis_page import PortfolioComparisonPanel
from nexo.ui.pages.assets_page import AssetsPage

A, B = Asset("PETR4"), Asset("VALE3")


@pytest.fixture
def asset_panel(qtbot, analytics_provider):
    panel = AssetAnalysisPanel(
        AnalyzeAsset(
            analytics_provider, analytics_provider, today=lambda: date(2026, 10, 6)
        )
    )
    qtbot.addWidget(panel)
    try:
        yield panel
    finally:
        analytics_provider.release.set()
        panel.runner.stop()
        panel.runner.wait()


def test_asset_analysis_real_values_explicit_yield_and_context_clear(
    asset_panel, qtbot
):
    panel = asset_panel
    assert not panel.yield_input.text()
    panel.yield_input.setText("6")
    panel.set_asset(A)
    qtbot.waitUntil(lambda: panel.analysis is not None, timeout=5000)
    assert panel.indicator_table.rowCount() == 10
    assert panel.valuation_table.item(1, 1).text() == "R$ 100,00"
    assert panel.valuation_table.item(1, 3).text() == "20,00%"
    assert "abaixo" in panel.valuation_table.item(1, 4).text()
    assert "2025-10-07" in panel.dividend_label.text()
    assert "252" in panel.risk_label.text() and "amostral" in panel.risk_label.text()
    assert panel.chart is not None
    panel.yield_input.setText("8")
    assert (
        panel.analysis is None
        and panel.chart is None
        and panel.indicator_table.rowCount() == 0
    )
    panel.calculate_button.click()
    qtbot.waitUntil(lambda: panel.analysis is not None, timeout=5000)
    assert panel.valuation_table.item(1, 1).text() == "R$ 75,00"
    assert "acima" in panel.valuation_table.item(1, 4).text()


def test_asset_context_rejects_late_result_and_network_does_not_block_gui(
    asset_panel, qtbot, analytics_provider
):
    analytics_provider.block_fund_next = True
    asset_panel.set_asset(A)
    qtbot.waitUntil(analytics_provider.entered.is_set, timeout=5000)
    beats = []
    QTimer.singleShot(0, lambda: beats.append(get_ident()))
    qtbot.waitUntil(lambda: bool(beats), timeout=5000)
    assert beats == [get_ident()] and not analytics_provider.release.is_set()
    asset_panel.set_asset(B)
    qtbot.waitUntil(
        lambda: asset_panel.analysis is not None and asset_panel.analysis.asset == B,
        timeout=5000,
    )
    analytics_provider.release.set()
    asset_panel.runner.wait()
    qtbot.waitUntil(lambda: not asset_panel.runner._jobs, timeout=5000)
    assert asset_panel.analysis.asset == B and "VALE3" in asset_panel.feedback.text()


def test_partial_asset_data_renders_unavailable_without_zero_or_demo(
    asset_panel, qtbot, analytics_provider
):
    analytics_provider.fund_error = MarketDataUnavailableError("Plano indisponível")
    asset_panel.yield_input.setText("6")
    asset_panel.set_asset(A)
    qtbot.waitUntil(lambda: asset_panel.analysis is not None, timeout=5000)
    assert asset_panel.valuation_table.item(0, 1).text() == "—"
    assert asset_panel.valuation_table.item(1, 1).text() == "R$ 100,00"
    assert "Plano indisponível" in asset_panel.feedback.text()


def test_asset_refresh_invalidates_before_parallel_quote_history_analysis(
    qtbot, analytics_database, analytics_provider
):
    cache = analytics_database[4]
    cache.get_quote(A)
    page = AssetsPage(
        get_quote=GetAssetQuote(cache),
        get_history=GetAssetHistory(cache),
        analyze_asset=AnalyzeAsset(cache, cache, today=lambda: date(2026, 10, 6)),
    )
    qtbot.addWidget(page)
    page.selected_asset = AssetSearchResult(A, "Petrobras", "BRL")
    analytics_provider.prices[A.symbol] = Decimal(90)
    try:
        page.refresh_asset(refresh=True)
        qtbot.waitUntil(
            lambda: page.quote is not None and page.analysis_panel.analysis is not None,
            timeout=5000,
        )
        assert page.quote.price == page.analysis_panel.analysis.quote.price == 90
        assert len(analytics_provider.calls) == 2
        assert len(analytics_provider.history_calls) == 1
    finally:
        page.runner.stop()
        page.analysis_panel.runner.stop()
        page.runner.wait()
        page.analysis_panel.runner.wait()


@pytest.fixture
def comparison_panel(qtbot, analytics_database, analytics_provider):
    ids, register, comparing, listing, _, _ = analytics_database
    register.execute(analytics_trade(ids[0]))
    register.execute(analytics_trade(ids[1], symbol="VALE3", quantity="20", price="20"))
    panel = PortfolioComparisonPanel(listing, comparing)
    qtbot.addWidget(panel)
    try:
        yield panel
    finally:
        analytics_provider.release.set()
        panel.runner.stop()
        panel.runner.wait()


def test_comparison_same_names_ids_real_metrics_and_context_clear(
    comparison_panel, qtbot
):
    panel = comparison_panel
    assert not panel.compare_button.isEnabled()
    for i in (0, 1):
        panel.portfolios.item(i).setSelected(True)
    assert panel.compare_button.isEnabled()
    panel.compare_button.click()
    qtbot.waitUntil(lambda: len(panel.comparison) == 2, timeout=5000)
    assert panel.table.horizontalHeaderItem(1).text() == "Igual • #1"
    assert panel.table.horizontalHeaderItem(2).text() == "Igual • #2"
    assert (
        panel.table.item(2, 1).text() == "R$ 300,00"
        and panel.table.item(3, 1).text() == "R$ 800,00"
    )
    assert (
        panel.table.item(8, 1).text() == "100,00%"
        and panel.positions_table.rowCount() == 2
    )
    assert panel.chart is not None
    panel.portfolios.item(0).setSelected(False)
    assert not panel.comparison and panel.chart is None and panel.table.rowCount() == 0


def test_comparison_late_result_ignored_after_selection_change(
    comparison_panel, qtbot, analytics_provider
):
    panel = comparison_panel
    analytics_provider.block_quotes_next = True
    for i in (0, 1):
        panel.portfolios.item(i).setSelected(True)
    panel.compare()
    qtbot.waitUntil(analytics_provider.entered.is_set, timeout=5000)
    panel.portfolios.item(0).setSelected(False)
    analytics_provider.release.set()
    panel.runner.wait()
    qtbot.waitUntil(lambda: not panel.runner._jobs, timeout=5000)
    assert (
        panel.comparison == () and panel.table.rowCount() == 0 and panel.chart is None
    )


def test_comparison_missing_quote_preserves_cost_and_explicit_ticker(
    comparison_panel, qtbot, analytics_provider
):
    del analytics_provider.prices["VALE3"]
    panel = comparison_panel
    for i in (0, 1):
        panel.portfolios.item(i).setSelected(True)
    panel.compare()
    qtbot.waitUntil(lambda: len(panel.comparison) == 2, timeout=5000)
    assert panel.table.item(2, 2).text() == "R$ 400,00"
    assert panel.table.item(3, 2).text() == "—" and panel.table.item(8, 2).text() == "—"
    assert "Sem valuation BRL: VALE3" in panel.feedback.text()
    assert panel.positions_table.item(1, 3).text() == "—"
    assert panel.chart.chart().series()[0].barSets()[0].count() == 1


@pytest.fixture
def analytics_window(qtbot, analytics_database, analytics_provider):
    from nexo.application.portfolio.create_portfolio import CreatePortfolio
    from nexo.application.portfolio.list_transactions import ListTransactions
    from nexo.application.portfolio.load_portfolio_positions import (
        LoadPortfolioPositions,
    )
    from nexo.application.portfolio.load_portfolio_valuation import (
        LoadPortfolioValuation,
    )
    from nexo.infrastructure.database.repositories.portfolio_repository import (
        SqlAlchemyPortfolioRepository,
    )
    from nexo.infrastructure.database.repositories.transaction_repository import (
        SqlAlchemyTransactionRepository,
    )
    from nexo.infrastructure.database.session import create_session_factory
    from nexo.ui.windows.main_window import MainWindow

    ids, register, comparing, listing, cache, engine = analytics_database
    factory = create_session_factory(engine)
    transactions = SqlAlchemyTransactionRepository(factory)
    positions = LoadPortfolioPositions(transactions)
    register.execute(analytics_trade(ids[0]))
    register.execute(analytics_trade(ids[1], symbol="VALE3"))
    window = MainWindow(
        CreatePortfolio(SqlAlchemyPortfolioRepository(factory)),
        listing,
        register,
        ListTransactions(transactions),
        positions,
        load_valuation=LoadPortfolioValuation(positions, cache),
        analyze_asset=AnalyzeAsset(cache, cache, today=lambda: date(2026, 10, 6)),
        compare_portfolios=comparing,
    )
    qtbot.addWidget(window)
    try:
        yield window
    finally:
        analytics_provider.release.set()
        window.close()
        window.wait_for_market()


def test_global_refresh_reloads_visible_asset_analysis(
    analytics_window, qtbot, analytics_provider
):
    window = analytics_window
    window.show_page(7)
    panel = window.analysis_page.asset_panel
    panel.yield_input.setText("6")
    panel.set_asset(A)
    qtbot.waitUntil(lambda: panel.analysis is not None, timeout=5000)
    assert panel.analysis.quote.price == 80
    analytics_provider.prices[A.symbol] = Decimal(90)
    window.refresh_market()
    qtbot.waitUntil(
        lambda: panel.analysis is not None and panel.analysis.quote.price == 90,
        timeout=5000,
    )
    assert panel.valuation_table.item(1, 3).text() == "10,00%"


def test_successful_trade_clears_comparison_and_rebuilds_on_next_compare(
    analytics_window, analytics_database, qtbot
):
    window = analytics_window
    panel = window.analysis_page.comparison_panel
    for i in (0, 1):
        panel.portfolios.item(i).setSelected(True)
    panel.compare()
    qtbot.waitUntil(lambda: len(panel.comparison) == 2, timeout=5000)
    assert panel.comparison[0].valuation.invested_cost == 300
    identity = analytics_database[0][0]
    trade = analytics_database[1].execute(
        analytics_trade(identity, quantity="2", price="20", hour=11)
    )
    window._transaction_created(trade)
    assert panel.comparison == () and panel.chart is None
    panel.compare()
    qtbot.waitUntil(lambda: len(panel.comparison) == 2, timeout=5000)
    assert panel.comparison[0].valuation.invested_cost == 340
    assert panel.comparison[0].transactions_count == 2
