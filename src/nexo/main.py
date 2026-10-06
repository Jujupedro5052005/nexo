import sys
from pathlib import Path
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox

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
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
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


def main(database_path: Path | None = None) -> int:
    """Start the Nexo desktop application."""
    application = create_application()
    try:
        engine = create_database_engine(database_path)
    except PortfolioRepositoryError:
        QMessageBox.critical(
            None, "Banco local", "Não foi possível abrir o banco local."
        )
        return 1
    provider = BrapiMarketDataProvider(MarketSettings.from_environment())
    window: MainWindow | None = None
    try:
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        repository = SqlAlchemyPortfolioRepository(session_factory)
        transactions = SqlAlchemyTransactionRepository(session_factory)
        load_positions = LoadPortfolioPositions(transactions)
        window = MainWindow(
            CreatePortfolio(repository),
            ListPortfolios(repository),
            RegisterTransaction(transactions),
            ListTransactions(transactions),
            load_positions,
            load_valuation=LoadPortfolioValuation(load_positions, provider),
            search_assets=SearchAssets(provider),
            get_quote=GetAssetQuote(provider),
            get_history=GetAssetHistory(provider),
        )
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
            window.wait_for_market()
        provider.close()
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
