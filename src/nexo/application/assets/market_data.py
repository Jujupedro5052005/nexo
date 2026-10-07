from collections.abc import Callable

from nexo.domain.interfaces.market_data_provider import MarketDataProvider
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.domain.models.market_integration import MarketIntegrationStatus


class GetAssetQuote:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def get_integration_status(self) -> MarketIntegrationStatus | None:
        return self._provider.get_integration_status()

    def invalidate_cache(self, asset: Asset) -> None:
        self._provider.invalidate(asset)

    def execute(
        self, asset: Asset, *, refresh: bool = False, explicit: bool = False
    ) -> Quote:
        if refresh:
            return self.prepare_refresh(asset)()
        with self._provider.refresh_context(explicit):
            return self._provider.get_quote(asset)

    def prepare_refresh(self, asset: Asset) -> Callable[[], Quote]:
        """Invalidate once before submitting parallel UI tasks; run remote I/O in worker."""
        self.invalidate_cache(asset)

        def load() -> Quote:
            with self._provider.refresh_context(True):
                return self._provider.get_quote(asset)

        return load


class SearchAssets:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(
        self, query: str, *, explicit: bool = False
    ) -> tuple[AssetSearchResult, ...]:
        with self._provider.refresh_context(explicit):
            return self._provider.search_assets(query.strip())


class GetAssetHistory:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(
        self, asset: Asset, period: str = "1mo", *, explicit: bool = False
    ) -> PriceHistory:
        with self._provider.refresh_context(explicit):
            return self._provider.get_history(asset, period)
