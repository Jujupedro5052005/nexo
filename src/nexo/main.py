import argparse
import sys
from pathlib import Path
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.assets.market_integration import (
    GetMarketIntegrationStatus,
    TestMarketConnection,
)
from nexo.application.assets.provider_status import GetProviderHealth
from nexo.application.portfolio.compare_portfolios import ComparePortfolios
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.demo_dataset import DEMO_NOTICE, ensure_demo_dataset
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
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
from nexo.infrastructure.market_data.composition import ProviderServices
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.ui.styles.theme import APP_STYLE
from nexo.ui.windows.main_window import MainWindow


def create_application() -> QApplication:
    """Create the Qt application and configure its presentation metadata."""
    instance = QApplication.instance()
    application = (
        QApplication(sys.argv) if instance is None else cast(QApplication, instance)
    )

    QCoreApplication.setApplicationName("Nexo Invest")
    QCoreApplication.setApplicationVersion("0.1.0")
    QCoreApplication.setOrganizationName("Nexo")
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLE)
    return application


def main(database_path: Path | None = None, *, demo: bool = False) -> int:
    """Start the Nexo desktop application."""
    application = create_application()
    if demo:
        if database_path is not None:
            raise ValueError("--demo usa exclusivamente data/nexo_demo.db.")
        database_path = ensure_demo_dataset()
    try:
        engine = create_database_engine(database_path)
    except PortfolioRepositoryError:
        QMessageBox.critical(
            None, "Banco local", "Não foi possível abrir o banco local."
        )
        return 1
    providers = ProviderServices(
        MarketSettings.from_environment(), Path(__file__).resolve().parents[2] / "data"
    )
    provider, cached = providers.brapi, providers.market
    window: MainWindow | None = None
    try:
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        repository = SqlAlchemyPortfolioRepository(session_factory)
        transactions = SqlAlchemyTransactionRepository(session_factory)
        load_positions = LoadPortfolioPositions(transactions)
        valuation = LoadPortfolioValuation(load_positions, cached)
        window = MainWindow(
            CreatePortfolio(repository),
            ListPortfolios(repository),
            RegisterTransaction(transactions),
            ListTransactions(transactions),
            load_positions,
            load_valuation=valuation,
            search_assets=SearchAssets(cached),
            get_quote=GetAssetQuote(cached),
            get_history=GetAssetHistory(cached),
            analyze_asset=AnalyzeAsset(
                cached,
                providers.fundamentals,
                dividends=providers.dividends,
                official=providers.official,
                actions=providers.actions,
            ),
            provider_health=GetProviderHealth(providers.health),
            integration_status=GetMarketIntegrationStatus(provider),
            test_connection=TestMarketConnection(provider),
            compare_portfolios=ComparePortfolios(
                ListPortfolios(repository), ListTransactions(transactions), valuation
            ),
        )
        if demo:
            window.setWindowTitle(f"Nexo Invest — {DEMO_NOTICE}")
            window.statusBar().showMessage(DEMO_NOTICE)
            portfolios = repository.list_all()
            if portfolios and portfolios[0].id is not None:
                window._select_portfolio(portfolios[0].id)
        window.show()
        return application.exec()
    except PortfolioRepositoryError:
        QMessageBox.critical(
            None, "Banco local", "Não foi possível abrir o banco local."
        )
        return 1
    finally:
        if window is not None:
            window.market_runner.stop()
            window.assets_page.runner.stop()
            window.assets_page.analysis_panel.runner.stop()
            window.analysis_page.stop()
            window.settings_page.market_panel.runner.stop()
            window.wait_for_market()
        providers.close()
        engine.dispose()


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nexo Invest — aplicação desktop")
    parser.add_argument("--demo", action="store_true", help="Abrir o banco separado de demonstração")
    args = parser.parse_args(argv)
    return main(demo=args.demo)


if __name__ == "__main__":
    raise SystemExit(cli())
