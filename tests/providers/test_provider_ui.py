import json
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest
from test_adapters_and_routing import bolsai, yahoo

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.assets.provider_status import GetProviderHealth
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.models.transaction import Transaction
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
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.infrastructure.market_data.routing import (
    RoutedDividendDataProvider,
    RoutedFundamentalDataProvider,
    RoutedMarketDataProvider,
)
from nexo.ui.components.market_snapshot_panel import MarketSnapshotPanel
from nexo.ui.components.provider_health_panel import ProviderHealthPanel
from nexo.ui.styles.theme import APP_STYLE
from nexo.ui.windows.main_window import MainWindow


@pytest.mark.parametrize("eod", [False, True])
def test_snapshot_price_variation_ohlcv_source_latency_freshness_and_json(qtbot, eod):
    panel = MarketSnapshotPanel()
    qtbot.addWidget(panel)
    now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    quote = Quote(
        Asset("B3SA3"),
        Decimal("12.34"),
        "BRL",
        "B3 S.A.",
        now,
        market_time=now if not eod else None,
        change=Decimal("0.1"),
        change_percent=Decimal("1.2"),
        day_high=Decimal(13),
        day_low=Decimal(12),
        volume=12345,
        market_cap=Decimal(1000000),
        latency_ms=Decimal(216),
        estimated_delay_minutes=30 if not eod else None,
        source="bolsai" if eod else "brapi",
        price_kind="eod" if eod else "delayed",
    )
    panel.display(quote)
    assert panel.price.text() == "R$ 12,34" and "1,2%" in panel.change.text()
    assert panel.metrics["high"].value_label.text() == "R$ 13,00"
    assert panel.metrics["volume"].value_label.text() == "12.345"
    assert "216 ms" in panel.status.text() and "tempo real" not in panel.status.text()
    assert ("EOD" if eod else "30 min") in panel.details.text()
    data = json.loads(panel.technical.toPlainText())
    assert data["symbol"] == "B3SA3" and data["latency_ms"] == "216"
    assert not any(k.lower() in {"authorization", "api_key", "cookies"} for k in data)
    panel.show()
    panel.toggle.click()
    assert panel.technical.isVisible()
    panel.toggle.click()
    assert not panel.technical.isVisible()
    panel.clear()
    assert panel.price.text() == "—" and not panel.technical.toPlainText()


def test_snapshot_partial_data_stays_absent(qtbot):
    panel = MarketSnapshotPanel()
    qtbot.addWidget(panel)
    panel.display(
        Quote(Asset("B3SA3"), Decimal(12), "BRL", "B3", datetime.now(timezone.utc))
    )
    assert all(c.value_label.text() == "—" for c in panel.metrics.values())
    data = json.loads(panel.technical.toPlainText())
    assert data["market_cap"] is data["day_high"] is data["volume"] is None


def test_refresh_without_portfolios_does_not_authorize_a_later_automatic_request(
    qtbot, portfolio_repository
):
    window = MainWindow(
        CreatePortfolio(portfolio_repository), ListPortfolios(portfolio_repository)
    )
    qtbot.addWidget(window)
    try:
        window.refresh_market()
        assert not window._explicit_market_refresh
    finally:
        window.close()
        window.wait_for_market()


def test_provider_health_local_snapshot_contains_no_secrets(qtbot, policy):
    policy.usage.reserve("bolsai", "fundamentals")
    policy.remaining["bolsai"] = 198
    case = GetProviderHealth(
        lambda: tuple(policy.health(p, True, "role") for p in policy.usage.budgets)
    )
    panel = ProviderHealthPanel(case)
    qtbot.addWidget(panel)
    text = " ".join(label.text() for label in panel.labels)
    assert "198" in text and "1/40" in text and "hit rate" in text
    assert "fixture-only" not in text and "Authorization" not in text


def test_repeated_assets_analysis_overview_portfolios_share_cache(
    qtbot, tmp_path, policy, record_property
):
    engine = create_database_engine(tmp_path / "economy.db")
    initialize_database(engine)
    sessions = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(sessions)
    transactions = SqlAlchemyTransactionRepository(sessions)
    identity = portfolios.add(Portfolio("Economia de quota")).id
    asset = Asset("B3SA3")
    register = RegisterTransaction(transactions)
    register.execute(
        Transaction(
            identity,
            asset,
            TransactionType.BUY,
            Decimal(10),
            Decimal(10),
            Decimal(0),
            datetime(2026, 10, 1, 12),  # noqa: DTZ001 -- ledger local wall time.
        )
    )
    remote_calls = []

    def handler(request):
        remote_calls.append(request.url.path)
        if request.url.path.endswith("tickers"):
            payload = {
                "results": [{"symbol": "B3SA3", "name": "B3 S.A.", "currency": "BRL"}]
            }
        elif request.url.path.endswith("historical"):
            payload = {
                "results": [
                    {
                        "symbol": "B3SA3",
                        "data": {
                            "historicalDataPrice": [
                                {"date": "2026-10-01T12:00:00Z", "close": 12},
                                {"date": "2026-10-02T12:00:00Z", "close": 13},
                            ]
                        },
                    }
                ]
            }
        else:
            payload = {
                "results": [
                    {
                        "symbol": "B3SA3",
                        "data": {
                            "regularMarketPrice": 12,
                            "currency": "BRL",
                            "regularMarketDayHigh": 13,
                            "regularMarketDayLow": 11,
                            "regularMarketVolume": 100,
                            "marketCap": 1000000,
                        },
                    }
                ]
            }
        return httpx.Response(200, json=payload)

    primary = BrapiMarketDataProvider(
        MarketSettings(token="fixture-only"),
        usage=policy.usage,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    fallback, bolsai_calls = bolsai(
        policy, {"queried_ticker": "B3SA3", "lpa": 1, "vpa": 10, "pl": 12}
    )
    yf, yahoo_calls = yahoo(policy)
    market = RoutedMarketDataProvider(primary, fallback, yf, policy)
    fundamentals = RoutedFundamentalDataProvider(fallback, None, policy)
    dividends = RoutedDividendDataProvider(yf, primary, policy)
    analysis = AnalyzeAsset(market, fundamentals, dividends=dividends)
    positions = LoadPortfolioPositions(transactions)
    window = MainWindow(
        CreatePortfolio(portfolios),
        ListPortfolios(portfolios),
        register,
        ListTransactions(transactions),
        positions,
        load_valuation=LoadPortfolioValuation(positions, market),
        search_assets=SearchAssets(market),
        get_quote=GetAssetQuote(market),
        get_history=GetAssetHistory(market),
        analyze_asset=analysis,
    )
    qtbot.addWidget(window)
    window.setStyleSheet(APP_STYLE)
    try:
        window._select_portfolio(identity)
        qtbot.waitUntil(
            lambda: window.overview_page.valuation_chart is not None, timeout=5000
        )
        window.assets_page.search_input.setText("B3SA3")
        window.assets_page.search()
        qtbot.waitUntil(lambda: window.assets_page.table.rowCount() == 1, timeout=5000)
        window.assets_page.table.selectRow(0)
        qtbot.waitUntil(
            lambda: window.assets_page.analysis_panel.analysis is not None, timeout=5000
        )
        for _ in range(3):
            for index in (2, 7, 0, 1):
                window.show_page(index)
            window.assets_page.refresh_asset()
            window.analysis_page.asset_panel.analyze()
            qtbot.waitUntil(
                lambda: (
                    window.assets_page.analysis_panel.analysis is not None
                    and window.analysis_page.asset_panel.analysis is not None
                ),
                timeout=5000,
            )
        assert len(remote_calls) == 3  # One quote, one search, one short history.
        assert "brapi" in window.assets_page.history_source_badge.text()
        assert len(bolsai_calls) == len(yahoo_calls) == 1
        assert policy.usage.count("brapi") == 3 and policy.usage.count("bolsai") == 1
        assert policy.health("brapi", True, "market").cache_hits >= 6
        record_property(
            "UI actions",
            "3 ciclos Ativos/Análises/Overview/Carteiras + consultas repetidas",
        )
        record_property(
            "mocked remote operations", "brapi=3; bolsai=1; Yahoo=1; CVM=0; internet=0"
        )
        record_property(
            "cache hits brapi", policy.health("brapi", True, "market").cache_hits
        )
    finally:
        window.close()
        window.wait_for_market()
        engine.dispose()


def test_explicit_quote_refresh_can_cross_local_budget_and_cache_does_not(
    qtbot, policy
):
    from test_adapters_and_routing import brapi

    primary, requests = brapi(
        policy,
        {
            "results": [
                {
                    "symbol": "ITSA4",
                    "data": {"regularMarketPrice": 10, "currency": "BRL"},
                }
            ]
        },
    )
    policy.usage.budgets["brapi"] = 1
    market = RoutedMarketDataProvider(primary, None, None, policy)
    case = GetAssetQuote(market)
    assert case.execute(Asset("ITSA4")).price == 10
    assert case.execute(Asset("ITSA4")).price == 10 and len(requests) == 1
    assert case.execute(Asset("ITSA4"), refresh=True).price == 10 and len(requests) == 2


def test_snapshot_old_data_is_cleared_between_selections(qtbot):
    panel = MarketSnapshotPanel()
    qtbot.addWidget(panel)
    q = Quote(
        Asset("B3SA3"),
        Decimal(12),
        "BRL",
        "B3",
        datetime.now(timezone.utc),
        day_high=Decimal(13),
    )
    panel.display(q)
    panel.display(replace(q, asset=Asset("ITSA4"), name="ITAUSA", day_high=None))
    assert (
        panel.metrics["high"].value_label.text() == "—"
        and panel.symbol.text() == "ITSA4"
    )
