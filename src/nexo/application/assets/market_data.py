from nexo.domain.interfaces.market_data_provider import MarketDataProvider
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote


class GetAssetQuote:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(self, asset: Asset) -> Quote:
        return self._provider.get_quote(asset)


class SearchAssets:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(self, query: str) -> tuple[AssetSearchResult, ...]:
        return self._provider.search_assets(query.strip())


class GetAssetHistory:
    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def execute(self, asset: Asset, period: str = "1mo") -> PriceHistory:
        return self._provider.get_history(asset, period)
