from datetime import timedelta
from decimal import Decimal

from presentation_market import PresentationMarketData

from nexo.application.portfolio.account import PortfolioAccount
from nexo.application.portfolio.performance import LoadPortfolioPerformance
from nexo.demo_dataset import ENTRY_PRICES, create_demo_dataset
from nexo.domain.models.asset import Asset
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.infrastructure.database.demo_finances import seed_demo_finances
from nexo.infrastructure.database.repositories.personal_finance import (
    SqlPersonalFinanceRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


def test_presentation_accounts_equity_and_user_changes_survive_restart(tmp_path):
    path = tmp_path / "nexo_demo.db"
    create_demo_dataset(path)
    engine = create_database_engine(path)
    market = PresentationMarketData()
    try:
        seed_demo_finances(engine)
        factory = create_session_factory(engine)
        repo = SqlAlchemyTransactionRepository(factory)
        account = PortfolioAccount(repo, repo, market)
        before = {}
        for identity in (1, 2, 3):
            snapshot = account.load(identity, quoted=True)
            assert snapshot.cash.balance > 0
            assert snapshot.equity == snapshot.cash.balance + snapshot.market_value
            assert len(snapshot.events) == 7
            performance = LoadPortfolioPerformance(repo, repo, market).execute(identity)
            assert performance.twr is not None, performance.issues
            before[identity] = snapshot
        original = before[1]
        account.register(
            PortfolioEvent(
                1,
                PortfolioEventType.DEPOSIT,
                max(e.occurred_at for e in original.events) + timedelta(days=1),
                Decimal("123.45"),
            )
        )
        finances = SqlPersonalFinanceRepository(factory)
        records = finances.budget_entries(), finances.goals(), finances.alerts()
    finally:
        engine.dispose()
    engine = create_database_engine(path)
    try:
        seed_demo_finances(engine)
        factory = create_session_factory(engine)
        repo = SqlAlchemyTransactionRepository(factory)
        account = PortfolioAccount(repo, repo, market)
        assert account.load(
            1, quoted=True
        ).cash.balance == original.cash.balance + Decimal("123.45")
        assert len(repo.list_events(1)) == 8
        for identity in (2, 3):
            assert account.load(identity, quoted=True) == before[identity]
        finances = SqlPersonalFinanceRepository(factory)
        assert (
            finances.budget_entries(),
            finances.goals(),
            finances.alerts(),
        ) == records
        assert not (tmp_path / "nexo.db").exists()
    finally:
        engine.dispose()


def test_presentation_catalog_sources_and_terminal_prices():
    market = PresentationMarketData()
    for symbol in ENTRY_PRICES:
        asset = Asset(symbol)
        quote = market.get_quote(asset)
        history = market.get_history(asset, "1y")
        assert history.points[-1].close == quote.price
        assert "fictícios" in quote.source == history.source
        fundamentals = market.get_fundamentals(asset)
        assert fundamentals.source == quote.source
        assert market.search_assets(symbol)[0].asset == asset
        dividends = market.get_dividends(
            asset, market.as_of.date() - timedelta(days=365), market.as_of.date()
        )
        assert dividends.source == quote.source
        assert all(e.verified is False for e in dividends.events)
    batch = market.get_quotes((Asset("INVALID4"), Asset("PETR4")))
    assert len(batch.quotes) == len(batch.issues) == 1
