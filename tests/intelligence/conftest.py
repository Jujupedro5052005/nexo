from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from nexo.application.intelligence.tools import FinancialTools
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary
from nexo.domain.models.market_data import Quote
from nexo.infrastructure.intelligence.composition import create_workspace
from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.storage import SqliteIntelligenceStorage


@pytest.fixture
def storage(tmp_path):
    return SqliteIntelligenceStorage(tmp_path / "ai.db")


@pytest.fixture
def workspace(storage, portfolio_repository):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    quote = Quote(
        Asset("ITUB4"),
        Decimal(30),
        "BRL",
        "Itaú",
        now,
        now,
        source="fixture · não mercado real",
    )
    fundamentals = CompanyFundamentals(
        Asset("ITUB4"), now, eps=Decimal(3), bvps=Decimal(20), source="fixture"
    )
    summary = DividendSummary(
        Asset("ITUB4"), (), now.date(), now.date(), now, source="fixture"
    )
    tools = FinancialTools(
        ListPortfolios(portfolio_repository),
        SimpleNamespace(execute=lambda identity: {"positions": []}),
        SimpleNamespace(execute=lambda identity: SimpleNamespace(concentration=None)),
        SimpleNamespace(execute=lambda asset: quote),
        SimpleNamespace(execute=lambda asset, period: {"points": []}),
        SimpleNamespace(get_fundamentals=lambda asset: fundamentals),
        SimpleNamespace(get_dividends=lambda asset, start, end: summary),
        storage,
    )
    return create_workspace(AISettings(provider="mock"), storage, tools, include_library=False)
