from datetime import datetime
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import inspect

from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
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


def database(path):
    engine = create_database_engine(path)
    initialize_database(engine)
    factory = create_session_factory(engine)
    return (
        engine,
        SqlAlchemyPortfolioRepository(factory),
        SqlAlchemyTransactionRepository(factory),
    )


def trade(
    identity,
    symbol="PETR4",
    quantity="10",
    price="30",
    kind=TransactionType.BUY,
    fees="0",
    hour=10,
):
    return Transaction(
        identity,
        Asset(symbol),
        kind,
        Decimal(quantity),
        Decimal(price),
        Decimal(fees),
        datetime(2026, 1, 1, hour),  # noqa: DTZ001 - Preserve ledger historical wall time.
    )


def test_application_use_cases_use_only_provider_contract(provider):
    asset = Asset("PETR4")
    assert GetAssetQuote(provider).execute(asset).price == 40
    assert SearchAssets(provider).execute(" PETR ")[0].asset == asset
    assert provider.searches == ["PETR"]
    assert len(GetAssetHistory(provider).execute(asset, "1y").points) == 2
    assert provider.histories == [(asset, "1y")]


def test_many_portfolios_share_one_deduplicated_quote_batch(tmp_path, provider):
    engine, portfolios, transactions = database(tmp_path / "batch.db")
    try:
        first = portfolios.add(Portfolio("First")).id
        second = portfolios.add(Portfolio("Second")).id
        register = RegisterTransaction(transactions)
        register.execute(trade(first))
        register.execute(trade(second))
        register.execute(trade(second, "VALE3"))
        values = LoadPortfolioValuation(
            LoadPortfolioPositions(transactions), provider
        ).execute_many([first, second, first])
        assert provider.calls == [(Asset("PETR4"), Asset("VALE3"))]
        assert values[first].current_market_value == 400
        assert values[second].current_market_value == 800
    finally:
        engine.dispose()


def test_portfolio_without_open_positions_needs_no_quotes(tmp_path, provider):
    engine, portfolios, transactions = database(tmp_path / "empty.db")
    try:
        identity = portfolios.add(Portfolio("Empty")).id
        value = LoadPortfolioValuation(
            LoadPortfolioPositions(transactions), provider
        ).execute(identity)
        assert value.current_market_value == 0 and not provider.calls
    finally:
        engine.dispose()


def test_provider_failure_leaves_ledger_metrics_available(tmp_path, provider):
    engine, portfolios, transactions = database(tmp_path / "offline.db")
    try:
        identity = portfolios.add(Portfolio("Local")).id
        RegisterTransaction(transactions).execute(trade(identity))
        provider.error = MarketDataUnavailableError("Offline")
        value = LoadPortfolioValuation(
            LoadPortfolioPositions(transactions), provider
        ).execute(identity)
        assert value.invested_cost == 300 and value.realized_profit_loss == 0
        assert (
            value.current_market_value is None
            and len(transactions.list_by_portfolio(identity)) == 1
        )
    finally:
        engine.dispose()


def test_sqlite_to_real_adapter_contract_reopens_without_persisting_quotes(tmp_path):
    path = tmp_path / "integrated.db"
    engine, portfolios, transactions = database(path)
    price = "40"
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "symbol": "PETR4",
                        "requestedSymbol": "PETR4",
                        "data": {
                            "regularMarketPrice": price,
                            "currency": "BRL",
                            "regularMarketTime": "2026-10-06T12:00:00Z",
                        },
                    }
                ]
            },
        )

    api = BrapiMarketDataProvider(
        client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    try:
        identity = portfolios.add(Portfolio("Integrated")).id
        register = RegisterTransaction(transactions)
        register.execute(trade(identity, price="30", fees="2"))
        register.execute(trade(identity, price="40", fees="2", hour=11))
        register.execute(
            trade(
                identity,
                quantity="5",
                price="42",
                kind=TransactionType.SELL,
                fees="1",
                hour=12,
            )
        )
        value = LoadPortfolioValuation(
            LoadPortfolioPositions(transactions), api
        ).execute(identity)
        assert (
            value.invested_cost,
            value.current_market_value,
            value.realized_profit_loss,
            value.unrealized_profit_loss,
            value.total_profit_loss,
        ) == (Decimal(528), Decimal(600), Decimal(33), Decimal(72), Decimal(105))
        assert set(inspect(engine).get_table_names()) == {"portfolios", "transactions"}
        assert all(
            "price" not in c["name"] or c["name"] == "unit_price"
            for c in inspect(engine).get_columns("transactions")
        )
    finally:
        engine.dispose()
    engine, _, transactions = database(path)
    try:
        price = "45"
        value = LoadPortfolioValuation(
            LoadPortfolioPositions(transactions), api
        ).execute(identity)
        assert value.current_market_value == 675 and value.total_profit_loss == 180
        assert len(transactions.list_by_portfolio(identity)) == 3 and len(requests) == 2
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "env,expected,size",
    [
        ({}, None, 1),
        ({"BRAPI_TOKEN": " primary ", "BRAPI_API_KEY": "alias"}, "primary", 1),
        ({"BRAPI_API_KEY": "alias"}, "alias", 1),
        ({"BRAPI_BATCH_SIZE": "oops"}, None, 1),
        ({"BRAPI_BATCH_SIZE": "0"}, None, 1),
        ({"BRAPI_BATCH_SIZE": "1000"}, None, 100),
    ],
)
def test_external_configuration_and_optional_token(monkeypatch, env, expected, size):
    monkeypatch.setattr(
        "nexo.infrastructure.market_data.config.load_dotenv",
        lambda *args, **kwargs: False,
    )
    for key in ("BRAPI_TOKEN", "BRAPI_API_KEY", "BRAPI_BATCH_SIZE"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    settings = MarketSettings.from_environment()
    assert settings.token == expected and settings.batch_size == size
