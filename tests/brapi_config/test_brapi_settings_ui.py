from threading import Event, get_ident

import httpx
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel
from test_integration_status import quote_payload

from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.assets.market_integration import GetMarketIntegrationStatus
from nexo.application.assets.market_integration import (
    TestMarketConnection as CheckConnection,
)
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.ui.components.market_integration_panel import MarketIntegrationPanel
from nexo.ui.windows.main_window import MainWindow


@pytest.fixture
def configuration_window(qtbot, portfolio_repository):
    def handler(request):
        if request.url.path == "/api/v2/tickers":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"symbol": "ITSA3", "longName": "Itaúsa", "currency": "BRL"}
                    ]
                },
            )
        return httpx.Response(200, json=quote_payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        window = MainWindow(
            CreatePortfolio(portfolio_repository),
            ListPortfolios(portfolio_repository),
            search_assets=SearchAssets(raw),
            get_quote=GetAssetQuote(raw),
            get_history=GetAssetHistory(raw),
            integration_status=GetMarketIntegrationStatus(raw),
            test_connection=CheckConnection(raw),
        )
        qtbot.addWidget(window)
        try:
            yield window
        finally:
            window.close()
            window.wait_for_market()


def test_settings_show_real_sandbox_capability_and_connection_result(
    configuration_window, qtbot
):
    window = configuration_window
    window.show_page(9)
    panel = window.settings_page.market_panel
    assert "brapi" in panel.provider_label.text()
    assert "Não configurado" in panel.configuration_label.text()
    assert "Sandbox público" in panel.mode_label.text()
    assert all(
        symbol in panel.feedback.text() for symbol in panel.status.public_symbols
    )
    panel.test_button.click()
    qtbot.waitUntil(lambda: panel.status.state == "connected", timeout=5000)
    assert "sandbox" in panel.feedback.text()
    assert panel.test_button.isEnabled()


def test_itsa3_search_then_configuration_required_with_direct_navigation(
    configuration_window, qtbot
):
    window = configuration_window
    window.show_page(2)
    page = window.assets_page
    page.search_input.setText("ITSA")
    page.search()
    qtbot.waitUntil(lambda: page.table.rowCount() == 1, timeout=5000)
    page.table.selectRow(0)
    qtbot.waitUntil(
        lambda: "Dados de mercado indisponíveis para ITSA3" in page.quote_label.text(),
        timeout=5000,
    )
    assert "encontrado na busca" in page.quote_label.text()
    assert "exige autenticação" in page.quote_label.text()
    assert ".env" in page.quote_label.text() and page.quote is None
    assert "inexistente" not in page.quote_label.text()
    page.configure_button.click()
    assert (
        window.page_stack.currentIndex() == 9
        and window.page_stack.currentWidget() is window.settings_page
    )


@pytest.mark.parametrize(
    "http_status,state,message",
    [
        (401, "invalid_token", "não foi aceita"),
        (403, "plan_denied", "plano atual"),
        (429, "rate_limited", "limite de consultas"),
    ],
)
def test_settings_error_states_are_distinct_and_secret_free(
    qtbot, http_status, state, message
):
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(http_status, json={"error": "TEST_TOKEN"})
        )
    ) as client:
        raw = BrapiMarketDataProvider(MarketSettings(token="TEST_TOKEN"), client=client)
        panel = MarketIntegrationPanel(
            GetMarketIntegrationStatus(raw), CheckConnection(raw)
        )
        qtbot.addWidget(panel)
        try:
            assert "Configurado" in panel.configuration_label.text()
            assert "a validar" in panel.mode_label.text()
            panel.test_button.click()
            qtbot.waitUntil(lambda: panel.status.state == state, timeout=5000)
            assert message in panel.feedback.text()
            assert all(
                "TEST_TOKEN" not in label.text() for label in panel.findChildren(QLabel)
            )
        finally:
            panel.runner.stop()
            panel.runner.wait()


def test_connection_request_does_not_block_gui(qtbot):
    entered, release = Event(), Event()

    def handler(request):
        entered.set()
        assert release.wait(10)
        return httpx.Response(200, json=quote_payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        panel = MarketIntegrationPanel(
            GetMarketIntegrationStatus(raw), CheckConnection(raw)
        )
        qtbot.addWidget(panel)
        try:
            panel.test_button.click()
            qtbot.waitUntil(entered.is_set, timeout=5000)
            assert not panel.test_button.isEnabled()
            beats = []
            QTimer.singleShot(0, lambda: beats.append(get_ident()))
            qtbot.waitUntil(lambda: bool(beats), timeout=5000)
            assert beats == [get_ident()] and not release.is_set()
            release.set()
            qtbot.waitUntil(lambda: panel.status.state == "connected", timeout=5000)
            assert panel.test_button.isEnabled()
        finally:
            release.set()
            panel.runner.stop()
            panel.runner.wait()


def test_unexpected_worker_error_is_not_shown_raw(qtbot):
    class BrokenTest:
        def execute(self):
            raise RuntimeError("TEST_TOKEN raw detail")

    panel = MarketIntegrationPanel(test_connection=BrokenTest())
    qtbot.addWidget(panel)
    try:
        panel.test_button.click()
        qtbot.waitUntil(lambda: panel.test_button.isEnabled(), timeout=5000)
        assert "Não foi possível testar" in panel.feedback.text()
        assert "TEST_TOKEN" not in panel.feedback.text()
    finally:
        panel.runner.stop()
        panel.runner.wait()
