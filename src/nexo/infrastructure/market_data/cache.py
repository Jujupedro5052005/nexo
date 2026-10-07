from collections.abc import Callable, Iterable
from datetime import date
from threading import Condition
from time import monotonic
from typing import Any, TypeVar, cast

from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import MarketDataProvider, QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.domain.models.market_integration import MarketIntegrationStatus

T = TypeVar("T")


class CachedMarketDataProvider(MarketDataProvider, FundamentalDataProvider):
    """Bounded memory cache, shared between pages; coalesces in-flight keys.

    No HTTP client, error caching, persistence or polling. Invalidation versions
    prevent an older in-flight fetch from repopulating a refreshed cache.
    """

    def __init__(
        self,
        market: MarketDataProvider,
        fundamentals: FundamentalDataProvider,
        *,
        quote_ttl: float = 30,
        history_ttl: float = 300,
        fundamental_ttl: float = 300,
        clock: Callable[[], float] = monotonic,
        max_entries: int = 256,
    ) -> None:
        self._market, self._fundamentals = market, fundamentals
        self.quote_ttl, self.history_ttl, self.fundamental_ttl = (
            quote_ttl,
            history_ttl,
            fundamental_ttl,
        )
        self._clock, self._max_entries = clock, max(1, max_entries)
        self._condition = Condition()
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}
        self._pending: set[tuple[Any, ...]] = set()
        self._epoch = 0

    def get_integration_status(self) -> MarketIntegrationStatus | None:
        return self._market.get_integration_status()

    def invalidate(self, asset: Asset | None = None) -> None:
        with self._condition:
            self._epoch += 1
            if asset is None:
                self._cache.clear()
            else:
                self._cache = {
                    key: entry for key, entry in self._cache.items() if key[1] != asset
                }

    def _cached(self, key: tuple[Any, ...]) -> Any:
        entry = self._cache.get(key)
        if entry is not None and entry[0] > self._clock():
            return entry[1]
        self._cache.pop(key, None)
        return None

    def _put(self, key: tuple[Any, ...], value: Any, ttl: float) -> None:
        if ttl <= 0:
            return
        self._cache[key] = (self._clock() + ttl, value)
        while len(self._cache) > self._max_entries:
            self._cache.pop(next(iter(self._cache)))

    def _get(self, key: tuple[Any, ...], operation: Callable[[], T], ttl: float) -> T:
        with self._condition:
            while key in self._pending:
                self._condition.wait()
            cached = self._cached(key)
            if cached is not None:
                return cast(T, cached)
            self._pending.add(key)
            epoch = self._epoch
        try:
            result = operation()
            with self._condition:
                if epoch == self._epoch:
                    self._put(key, result, ttl)
            return result
        finally:
            with self._condition:
                self._pending.discard(key)
                self._condition.notify_all()

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        assets = tuple(dict.fromkeys(assets))
        keys = [("quote", asset) for asset in assets]
        with self._condition:
            while any(key in self._pending for key in keys):
                self._condition.wait()
            cached: dict[Asset, Quote] = {
                asset: q
                for asset in assets
                if (q := self._cached(("quote", asset))) is not None
            }
            missing = tuple(asset for asset in assets if asset not in cached)
            pending = [("quote", asset) for asset in missing]
            self._pending.update(pending)
            epoch = self._epoch
        if not missing:
            return QuoteBatch(tuple(cached[asset] for asset in assets))
        try:
            batch = self._market.get_quotes(missing)
            with self._condition:
                for quote in batch.quotes:
                    if quote.asset in missing:
                        cached[quote.asset] = quote
                        if epoch == self._epoch:
                            self._put(("quote", quote.asset), quote, self.quote_ttl)
            return QuoteBatch(
                tuple(cached[a] for a in assets if a in cached), batch.issues
            )
        finally:
            with self._condition:
                self._pending.difference_update(pending)
                self._condition.notify_all()

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        return self._market.search_assets(query)

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        return self._get(
            ("history", asset, period),
            lambda: self._market.get_history(asset, period),
            self.history_ttl,
        )

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        return self._get(
            ("fundamentals", asset),
            lambda: self._fundamentals.get_fundamentals(asset),
            self.fundamental_ttl,
        )

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        return self._get(
            ("dividends", asset, start_date, end_date),
            lambda: self._fundamentals.get_dividends(asset, start_date, end_date),
            self.fundamental_ttl,
        )
