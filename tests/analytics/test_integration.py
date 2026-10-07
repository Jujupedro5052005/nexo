from datetime import date
from decimal import Decimal

import httpx
from analytics_helpers import analytics_trade
from sqlalchemy import inspect

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.portfolio.compare_portfolios import ComparePortfolios
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.domain.models.asset import Asset
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import create_session_factory
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.cache import CachedMarketDataProvider
from nexo.infrastructure.market_data.config import MarketSettings


def test_sqlite_http_adapter_analytics_comparison_and_refresh_without_derived_tables(
    analytics_database,
):
    ids, register, _, _, _, engine = analytics_database
    register.execute(analytics_trade(ids[0]))
    register.execute(analytics_trade(ids[1], symbol="VALE3", quantity="20", price="20"))
    register.execute(analytics_trade(ids[1], quantity="5"))
    prices = {"PETR4": 80, "VALE3": 40}
    requests = []

    def handler(request):
        requests.append(request.url.path)
        rows = []
        for symbol in request.url.params["symbols"].split(","):
            if request.url.path.endswith("/quote"):
                if symbol not in prices:
                    continue
                data = {
                    "regularMarketPrice": prices[symbol],
                    "currency": "BRL",
                    "regularMarketTime": "2026-10-06T12:00:00Z",
                }
            elif request.url.path.endswith("/statistics"):
                data = {
                    "trailingEps": 4,
                    "bookValue": 20,
                    "mostRecentQuarter": "2026-06-30",
                }
            elif request.url.path.endswith("/financial-data"):
                data = {
                    "totalRevenue": 1000,
                    "ebitda": 300,
                    "totalDebt": 200,
                    "totalCash": 100,
                    "returnOnEquity": 0.2,
                    "profitMargins": 0.25,
                }
            elif request.url.path.endswith("/dividends"):
                data = {
                    "cashDividends": [
                        {
                            "label": "DIVIDENDO",
                            "rate": 6,
                            "paymentDate": "2026-01-01",
                            "verified": True,
                        }
                    ]
                }
            else:
                data = {
                    "historicalDataPrice": [
                        {"date": f"2026-10-0{i}T12:00:00Z", "close": close}
                        for i, close in enumerate((100, 120, 90, 110), start=1)
                    ]
                }
            rows.append({"requestedSymbol": symbol, "symbol": symbol, "data": data})
        return httpx.Response(200, json={"results": rows})

    factory = create_session_factory(engine)
    portfolio_repository = SqlAlchemyPortfolioRepository(factory)
    transaction_repository = SqlAlchemyTransactionRepository(factory)
    listing = ListPortfolios(portfolio_repository)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        raw = BrapiMarketDataProvider(MarketSettings(), client=client)
        cache = CachedMarketDataProvider(raw, raw)
        analysis_case = AnalyzeAsset(cache, cache, today=lambda: date(2026, 10, 6))
        analysis = analysis_case.execute(Asset("PETR4"), required_yield=Decimal("0.06"))
        assert analysis.quote.price == 80 and analysis.bazin.price == 100
        assert analysis.bazin.margin.ratio == Decimal("0.2")
        assert analysis.risk.max_drawdown == Decimal("-0.25")
        valuation = LoadPortfolioValuation(
            LoadPortfolioPositions(transaction_repository), cache
        )
        comparing = ComparePortfolios(
            listing, ListTransactions(transaction_repository), valuation
        )
        first, second = comparing.execute(ids[:2])
        assert (
            first.valuation.invested_cost == 300
            and first.valuation.current_market_value == 800
        )
        assert (
            second.valuation.invested_cost == 550
            and second.valuation.current_market_value == 1200
        )
        assert second.valuation.concentration.largest.quantize(
            Decimal(".000001")
        ) == Decimal(".666667")
        assert requests.count("/api/v2/stocks/quote") == 2
        del prices["VALE3"]
        partial = comparing.execute(ids[:2], refresh=True)[1]
        assert (
            partial.valuation.current_market_value is None
            and partial.valuation.concentration.weights == ()
        )
        assert partial.valuation.concentration.unavailable_assets == ("VALE3",)
    assert len(transaction_repository.list_by_portfolio(ids[1])) == 2
    assert set(inspect(engine).get_table_names()) == {"portfolios", "transactions"}
