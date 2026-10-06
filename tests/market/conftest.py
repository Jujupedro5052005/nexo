from datetime import datetime, timezone
from decimal import Decimal
from threading import Event

import pytest

from nexo.domain.interfaces.market_data_provider import MarketDataProvider, QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import (
    AssetSearchResult,
    HistoricalPrice,
    PriceHistory,
    Quote,
)


class FakeProvider(MarketDataProvider):
    def __init__(self):
        self.price = Decimal(40)
        self.currency = "BRL"
        self.calls = []
        self.searches = []
        self.histories = []
        self.error = None
        self.history_error = None
        self.entered = Event()
        self.release = Event()
        self.block_next = False
        self.empty_history = False

    def get_quotes(self, assets):
        assets = tuple(assets)
        self.calls.append(assets)
        price = self.price
        if self.block_next:
            self.block_next = False
            self.entered.set()
            if not self.release.wait(10):
                raise RuntimeError("Test gate not released")
        if self.error:
            raise self.error
        now = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
        return QuoteBatch(
            tuple(
                Quote(
                    a,
                    price,
                    self.currency,
                    a.symbol,
                    now,
                    now,
                    Decimal(1),
                    Decimal("2.5"),
                    "fake",
                )
                for a in assets
            )
        )

    def search_assets(self, query):
        self.searches.append(query)
        if self.error:
            raise self.error
        return (
            AssetSearchResult(Asset("PETR4"), "Petrobras", "BRL", "stock"),
            AssetSearchResult(Asset("VALE3"), "Vale", "BRL", "stock"),
        )

    def get_history(self, asset, period):
        self.histories.append((asset, period))
        if self.history_error:
            raise self.history_error
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        points = (
            ()
            if self.empty_history
            else (
                HistoricalPrice(now, Decimal(30)),
                HistoricalPrice(
                    datetime(2026, 10, 7, tzinfo=timezone.utc), Decimal("31.5")
                ),
            )
        )
        return PriceHistory(asset, points, period, now, "fake")


@pytest.fixture
def provider():
    return FakeProvider()
