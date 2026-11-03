from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import inspect

from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.interfaces.market_data_provider import (
    MarketDataProvider,
    MarketDataUnavailableError,
    QuoteBatch,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.intelligence import AnalysisRequest, ToolCall
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


class FixtureMarket(MarketDataProvider):
    def get_quotes(self, assets):
        now = datetime.now(timezone.utc)
        return QuoteBatch(
            tuple(
                Quote(
                    asset, Decimal(20), "BRL", "Fixture", now, source="synthetic-test"
                )
                for asset in assets
            )
        )

    def search_assets(self, query):
        return ()

    def get_history(self, asset, period):
        raise MarketDataUnavailableError("Fixture sem histórico")


def test_tools_read_reconstructed_real_sqlite_ledger_without_mutations(
    workspace, tmp_path
):
    engine = create_database_engine(tmp_path / "ledger.db")
    try:
        initialize_database(engine)
        factory = create_session_factory(engine)
        portfolios = SqlAlchemyPortfolioRepository(factory)
        transactions = SqlAlchemyTransactionRepository(factory)
        selected = portfolios.add(Portfolio("Selecionada"))
        portfolios.add(Portfolio("Nome privado de outra carteira"))
        RegisterTransaction(transactions).execute(
            Transaction(
                selected.id,
                Asset("ITUB4"),
                TransactionType.BUY,
                Decimal(10),
                Decimal(15),
                Decimal(0),
                datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        initial_tables = inspect(engine).get_table_names()
        tools = workspace.orchestrator.tools
        tools.portfolios = ListPortfolios(portfolios)
        tools.positions = LoadPortfolioPositions(transactions)
        tools.valuation = LoadPortfolioValuation(tools.positions, FixtureMarket())
        tools.transactions = ListTransactions(transactions)
        request = AnalysisRequest(
            question="Analise a carteira", portfolio_id=selected.id
        )
        result = workspace.orchestrator.ask(request)
        snapshot = result.evidence[0].data
        assert snapshot["valuation"]["current_market_value"] == "200"
        assert snapshot["valuation"]["invested_cost"] == "150"
        assert snapshot["concentration"]["largest"] == "1"
        assert snapshot["cash_included"] is False
        recent = tools.execute(
            ToolCall(
                name="get_portfolio_transactions",
                arguments={"portfolio_id": selected.id, "limit": 1},
            ),
            request,
        )
        assert recent.available and recent.data["total_count"] == 1
        assert recent.data["transactions"][0]["asset"]["symbol"] == "ITUB4"
        visible = tools.execute(ToolCall(name="list_portfolios"), request)
        assert visible.data == [{"id": selected.id}]
        assert "Nome privado" not in result.model_dump_json()
        assert len(transactions.list_by_portfolio(selected.id)) == 1
        assert initial_tables == inspect(engine).get_table_names()
        assert "positions" not in initial_tables
    finally:
        engine.dispose()
