from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from threading import Event

import pytest

from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    MarketDataProvider,
    MarketDataUnavailableError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory, Quote

NOW = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)


class AnalyticsProvider(MarketDataProvider, FundamentalDataProvider):
    def __init__(self):
        self.prices = {"PETR4": Decimal(80), "VALE3": Decimal(40), "ITUB4": Decimal(20)}
        self.currency = "BRL"
        self.calls = []
        self.fund_calls = []
        self.div_calls = []
        self.history_calls = []
        self.fund_error = None
        self.div_error = None
        self.history_error = None
        self.market_error = None
        self.entered = Event()
        self.release = Event()
        self.block_fund_next = False
        self.block_quotes_next = False
        self.invalidations = []

    def invalidate(self, asset=None):
        self.invalidations.append(asset)

    def get_quotes(self, assets):
        assets = tuple(assets)
        self.calls.append(assets)
        if self.block_quotes_next:
            self.block_quotes_next = False
            self.entered.set()
            assert self.release.wait(15)
        if self.market_error:
            raise self.market_error
        return QuoteBatch(
            tuple(
                Quote(
                    a,
                    self.prices[a.symbol],
                    self.currency,
                    a.symbol,
                    NOW,
                    NOW,
                    source="fake",
                )
                for a in assets
                if a.symbol in self.prices
            ),
            tuple(
                QuoteIssue(a, MarketDataUnavailableError("Sem quote"))
                for a in assets
                if a.symbol not in self.prices
            ),
        )

    def search_assets(self, query):
        return ()

    def get_history(self, asset, period):
        self.history_calls.append((asset, period))
        if self.history_error:
            raise self.history_error
        return PriceHistory(
            asset,
            tuple(
                HistoricalPrice(NOW + timedelta(days=i), Decimal(value))
                for i, value in enumerate((100, 120, 90, 110))
            ),
            period,
            NOW,
            "fake",
        )

    def get_fundamentals(self, asset):
        self.fund_calls.append(asset)
        if self.block_fund_next:
            self.block_fund_next = False
            self.entered.set()
            assert self.release.wait(15)
        if self.fund_error:
            raise self.fund_error
        return CompanyFundamentals(
            asset,
            NOW,
            eps=Decimal(4),
            bvps=Decimal(20),
            roe=Decimal("0.2"),
            roa=Decimal("0.1"),
            net_margin=Decimal("0.25"),
            revenue=Decimal(1000),
            ebitda=Decimal(300),
            debt=Decimal(200),
            cash=Decimal(100),
            reference_date=date(2026, 6, 30),
            source="fake",
        )

    def get_dividends(self, asset, start_date, end_date):
        self.div_calls.append((asset, start_date, end_date))
        if self.div_error:
            raise self.div_error
        return DividendSummary(
            asset,
            (
                CashDividend(date(2026, 1, 1), Decimal(6), "DIVIDENDO", True),
                CashDividend(date(2026, 2, 1), Decimal(2), "JCP", True),
            ),
            start_date,
            end_date,
            NOW,
            source="fake",
        )


@pytest.fixture
def analytics_provider():
    provider = AnalyticsProvider()
    try:
        yield provider
    finally:
        provider.release.set()


@pytest.fixture
def analytics_database(tmp_path, analytics_provider):
    from nexo.application.portfolio.compare_portfolios import ComparePortfolios
    from nexo.application.portfolio.list_portfolios import ListPortfolios
    from nexo.application.portfolio.list_transactions import ListTransactions
    from nexo.application.portfolio.load_portfolio_positions import (
        LoadPortfolioPositions,
    )
    from nexo.application.portfolio.load_portfolio_valuation import (
        LoadPortfolioValuation,
    )
    from nexo.application.portfolio.register_transaction import RegisterTransaction
    from nexo.domain.models.portfolio import Portfolio
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
    from nexo.infrastructure.market_data.cache import CachedMarketDataProvider

    engine = create_database_engine(tmp_path / "analytics.db")
    initialize_database(engine)
    factory = create_session_factory(engine)
    portfolios = SqlAlchemyPortfolioRepository(factory)
    transactions = SqlAlchemyTransactionRepository(factory)
    ids = tuple(
        portfolios.add(Portfolio(name)).id for name in ("Igual", "Igual", "Vazia")
    )
    cache = CachedMarketDataProvider(analytics_provider, analytics_provider)
    valuation = LoadPortfolioValuation(LoadPortfolioPositions(transactions), cache)
    listing = ListPortfolios(portfolios)
    comparing = ComparePortfolios(listing, ListTransactions(transactions), valuation)
    try:
        yield ids, RegisterTransaction(transactions), comparing, listing, cache, engine
    finally:
        analytics_provider.release.set()
        engine.dispose()
