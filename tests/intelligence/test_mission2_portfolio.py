import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtGui import QFont, QFontDatabase

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.interfaces.market_data_provider import QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.intelligence import AnalysisRequest, IntelligenceError, utc_now
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
from nexo.infrastructure.intelligence.knowledge import load_canonical_library
from nexo.ui.styles.theme import APP_STYLE
from nexo.ui.windows.main_window import MainWindow

from .test_ledger_integration import FixtureMarket
from .test_mission2 import investigation_data  # noqa: F401 - registered pytest fixture


@pytest.fixture
def portfolio_investigation(investigation, tmp_path):
    engine = create_database_engine(tmp_path / "ledger.db")
    initialize_database(engine)
    sessions = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(sessions)
    transactions = SqlAlchemyTransactionRepository(sessions)
    selected = portfolios.add(Portfolio("Carteira de teste · dados sintéticos"))
    portfolios.add(Portfolio("Outra carteira privada"))
    for symbol in ("ITUB4", "PETR4", "EGIE3"):
        RegisterTransaction(transactions).execute(
            Transaction(
                selected.id,
                Asset(symbol),
                TransactionType.BUY,
                Decimal(10),
                Decimal(15),
                Decimal(0),
                utc_now() - timedelta(days=60),
            )
        )
    tools = investigation.orchestrator.tools
    tools.portfolios = ListPortfolios(portfolios)
    investigation.portfolios = tools.portfolios
    tools.positions = LoadPortfolioPositions(transactions)
    market = FixtureMarket()
    market.get_quotes = lambda assets: QuoteBatch(
        tuple(tools.quote.execute(a) for a in assets)
    )
    tools.valuation = LoadPortfolioValuation(tools.positions, market)
    yield investigation
    assert len(transactions.list_by_portfolio(selected.id)) == 3
    engine.dispose()


def test_whole_portfolio_has_every_position_risk_scenarios_and_exposure(
    portfolio_investigation,
):
    response = portfolio_investigation.ask(
        AnalysisRequest(
            question="Analise toda a minha carteira e identifique as melhores oportunidades nas condições atuais",
            portfolio_id=1,
        )
    )
    report = response.report
    assert len(report["assets"]) == 3
    assert report["calls"] == 13
    assert len(report["correlations"]) == 3
    assert all(c["value"] is not None for c in report["correlations"])
    assert set(report["sector_exposure"]) == {
        "Bancos",
        "Petróleo e gás",
        "Energia elétrica",
    }
    assert all(
        a["scenarios"] and a["cross_checks"] and a["risk"] for a in report["assets"]
    )
    assert all(a["verdict"] == "Evitar ampliar posição" for a in report["assets"])
    assert "Outra carteira privada" not in response.model_dump_json()


def test_deep_limit_is_checked_before_market(portfolio_investigation):
    portfolio_investigation.orchestrator.deep.max_assets = 2

    def forbidden(*args, **kwargs):
        pytest.fail("Budget deve ser verificado antes de mercado")

    portfolio_investigation.orchestrator.tools.valuation.execute = forbidden
    with pytest.raises(IntelligenceError, match="limite"):
        portfolio_investigation.ask(
            AnalysisRequest(question="Analise minha carteira", portfolio_id=1)
        )


def test_ticker_question_does_not_investigate_all_selected_positions(
    portfolio_investigation,
):
    result = portfolio_investigation.ask(
        AnalysisRequest(question="Qual é o preço teto de ITUB4?", portfolio_id=1)
    )
    assert [a["symbol"] for a in result.report["assets"]] == ["ITUB4"]
    assert result.report["calls"] == 5


def test_demo_is_explicit_and_context_is_separate(investigation):
    investigation.orchestrator.data_mode = "demo"
    response = investigation.ask(
        AnalysisRequest(question="Analise ITUB4", symbol="ITUB4", analysis_mode="deep")
    )
    assert response.report["data_mode"] == "demo"
    assert "DEMO" in response.markdown


@pytest.mark.parametrize("size", [(1440, 900), (1180, 720)])
def test_qt_review_at_standard_and_small_sizes(
    qtbot, qapp, portfolio_investigation, tmp_path, size
):
    saved_style, saved_font = qapp.styleSheet(), qapp.font()
    font = Path("C:/Windows/Fonts/segoeui.ttf")
    if font.exists():
        QFontDatabase.addApplicationFont(str(font))
        qapp.setFont(QFont("Segoe UI", 10))
    qapp.setStyleSheet(APP_STYLE)
    load_canonical_library(portfolio_investigation.storage)
    window = MainWindow(
        CreatePortfolio(portfolio_investigation.portfolios._repository),
        portfolio_investigation.portfolios,
        intelligence=portfolio_investigation,
    )
    page = window.intelligence_page
    qtbot.addWidget(window)
    try:
        window.resize(*size)
        window.show()
        window.show_page(9)
        page.portfolio.setCurrentIndex(1)
        page.deep_mode.setChecked(True)
        page.question.setPlainText("Analise toda a minha carteira")
        page.ask()
        qtbot.waitUntil(lambda: page._response is not None, timeout=10000)
        assert page.report_view.report["assets"]
        assert page.chat.viewport().height() >= 160
        output = Path(os.environ.get("NEXO_REVIEW_DIR", str(tmp_path)))
        output.mkdir(parents=True, exist_ok=True)
        assert window.grab().save(str(output / f"chat-{size[0]}.png"))
        page.tabs.setCurrentIndex(1)
        qtbot.wait(20)
        assert window.grab().save(str(output / f"report-{size[0]}.png"))
        scroll = page.tabs.widget(1)
        scroll.verticalScrollBar().setValue(650)
        qtbot.wait(20)
        assert window.grab().save(str(output / f"asset-cards-{size[0]}.png"))
        page.tabs.setCurrentIndex(2)
        qtbot.wait(20)
        assert window.grab().save(str(output / f"library-{size[0]}.png"))
    finally:
        page.runner.stop()
        page.runner.wait()
        window.close()
        window.wait_for_market()
        qapp.setStyleSheet(saved_style)
        qapp.setFont(saved_font)
