"""UI verification with explicit test doubles; demo mode never ships fake quotes."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.portfolio.compare_portfolios import ComparePortfolios
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.demo_dataset import DEMO_NOTICE, ENTRY_PRICES, create_demo_dataset
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import MarketDataProvider, QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.market_data import (
    AssetSearchResult,
    HistoricalPrice,
    PriceHistory,
    Quote,
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
)
from nexo.ui.windows.main_window import MainWindow

NOW = datetime(2026, 10, 7, 14, tzinfo=timezone.utc)


class PresentationTestProvider(MarketDataProvider, FundamentalDataProvider):
    def get_quotes(self, assets):
        return QuoteBatch(tuple(Quote(
            asset, Decimal(ENTRY_PRICES[asset.symbol][-1]), "BRL", asset.symbol, NOW,
            source="test fixture", open=Decimal(30), day_high=Decimal(40),
            day_low=Decimal(25), volume=100000, change=Decimal(1),
        ) for asset in assets))

    def search_assets(self, query):
        return (AssetSearchResult(Asset(query), query, "BRL", source="test fixture"),)

    def get_history(self, asset, period):
        return PriceHistory(asset, tuple(
            HistoricalPrice(NOW - timedelta(days=40-i), Decimal(30) + Decimal(i % 7))
            for i in range(40)
        ), period, NOW, "test fixture")

    def get_fundamentals(self, asset):
        return CompanyFundamentals(asset, NOW, source="test fixture", eps=Decimal(4),
                                   bvps=Decimal(20), revenue=Decimal(100), net_income=Decimal(20))

    def get_dividends(self, asset, start_date, end_date):
        return DividendSummary(asset, (
            CashDividend(end_date - timedelta(days=60), Decimal(2), "DIVIDENDO", True),
            CashDividend(end_date - timedelta(days=10), Decimal(1), "DIVIDENDO", True),
        ), start_date, end_date, NOW, source="test fixture")


@pytest.fixture
def presentation_window(tmp_path, qtbot):
    path = tmp_path / "nexo_demo.db"
    create_demo_dataset(path)
    engine = create_database_engine(path)
    factory = create_session_factory(engine)
    portfolio_repository = SqlAlchemyPortfolioRepository(factory)
    transactions = SqlAlchemyTransactionRepository(factory)
    listing = ListPortfolios(portfolio_repository)
    positions = LoadPortfolioPositions(transactions)
    provider = PresentationTestProvider()
    valuation = LoadPortfolioValuation(positions, provider)
    window = MainWindow(
        CreatePortfolio(portfolio_repository), listing, RegisterTransaction(transactions),
        ListTransactions(transactions), positions, load_valuation=valuation,
        search_assets=SearchAssets(provider), get_quote=GetAssetQuote(provider),
        get_history=GetAssetHistory(provider), analyze_asset=AnalyzeAsset(provider, provider),
        compare_portfolios=ComparePortfolios(listing, ListTransactions(transactions), valuation),
    )
    qtbot.addWidget(window)
    window.show()
    try:
        yield window
    finally:
        window.close()
        window.wait_for_market()
        engine.dispose()


def test_all_pages_and_three_portfolios_have_valid_data(presentation_window, qtbot):
    window = presentation_window
    for identity, assets, trades in ((1, 8, 35), (2, 7, 31), (3, 6, 27)):
        window._select_portfolio(identity)
        qtbot.waitUntil(lambda: len(window._market_values) == 3, timeout=10000)
        assert window.overview_page.positions_table.rowCount() == assets
        assert window.portfolios_page.positions_table.rowCount() == assets
        assert window.transactions_page.table.rowCount() == trades
        assert window.overview_page.valuation_chart is not None
        assert window.overview_page.concentration_panel.chart is not None
        assert window.portfolios_page.concentration_panel.chart is not None
        assert window.overview_page.metrics["market"].value_label.text() != "—"
    for index in range(10):
        window.show_page(index)
        assert window.page_stack.currentIndex() == index
    comparison = window.analysis_page.comparison_panel
    for index in range(comparison.portfolios.count()):
        comparison.portfolios.item(index).setSelected(True)
    comparison.compare()
    qtbot.waitUntil(lambda: len(comparison.comparison) == 3, timeout=10000)
    assert comparison.chart is not None
    assert comparison.positions_table.rowCount() == 21
    assert len({p.valuation.current_market_value for p in comparison.comparison}) == 3
    for portfolio in comparison.comparison:
        results = [p.unrealized_profit_loss for p in portfolio.valuation.positions]
        assert any(value > 0 for value in results) and any(value < 0 for value in results)


@pytest.mark.parametrize("symbol", ["PETR4", "B3SA3"])
def test_asset_history_dividends_and_valuation_charts(presentation_window, qtbot, symbol):
    window = presentation_window
    window.show_page(2)
    page = window.assets_page
    page.search_input.setText(symbol)
    page.search()
    qtbot.waitUntil(lambda: page.table.rowCount() == 1, timeout=10000)
    page.table.selectRow(0)
    qtbot.waitUntil(lambda: page.quote is not None and page.chart is not None
                   and page.analysis_panel.analysis is not None, timeout=10000)
    panel = page.analysis_panel
    panel.yield_input.setText("6")
    panel.analyze()
    qtbot.waitUntil(lambda: panel.analysis is not None, timeout=10000)
    assert panel.analysis.quote.source == "test fixture"
    assert panel.analysis.fundamentals is not None
    assert len(panel.analysis.dividends.events) == 2
    assert panel.analysis.graham.price > 0 and panel.analysis.bazin.price > 0
    assert panel.chart is not None and panel.indicator_table.rowCount() == 10
    assert len(page.history.points) == 40


@pytest.mark.parametrize("demo_mode", [False, True])
def test_real_entry_point_uses_separate_db_and_labels_demo(tmp_path, qtbot, monkeypatch, demo_mode):
    import nexo.demo_dataset as dataset
    import nexo.main as entry

    normal = tmp_path / "nexo.db"
    monkeypatch.setattr(dataset, "default_database_path", lambda: normal)
    provider = PresentationTestProvider()
    closed = []
    services = SimpleNamespace(
        brapi=provider, market=provider, fundamentals=provider, dividends=provider,
        official=None, actions=None, health=lambda: (), close=lambda: closed.append(True),
    )
    monkeypatch.setattr(entry, "ProviderServices", lambda *args: services)
    application = entry.create_application()

    def run():
        window = next(w for w in application.topLevelWidgets()
                      if isinstance(w, MainWindow) and w.isVisible())
        qtbot.addWidget(window)
        if demo_mode:
            assert window.selected_portfolio_id == 1
            assert window.overview_page.positions_table.rowCount() == 8
            assert DEMO_NOTICE in window.windowTitle()
            assert DEMO_NOTICE in window.statusBar().currentMessage()
            assert not normal.exists()
        else:
            assert window.selected_portfolio_id is None
            assert window.windowTitle() == "Nexo Invest"
            assert normal.exists()
            assert not (tmp_path / "nexo_demo.db").exists()
        window.close()
        return 0

    monkeypatch.setattr(application, "exec", run)
    assert entry.main(demo=True) == 0 if demo_mode else entry.main(normal) == 0
    assert closed == [True]
