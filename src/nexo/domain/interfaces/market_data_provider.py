from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass

from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.domain.models.market_integration import MarketIntegrationStatus


class MarketDataError(Exception):
    """Safe provider-independent boundary error."""


class MarketDataUnavailableError(MarketDataError):
    pass


class MarketOfflineError(MarketDataUnavailableError):
    """Connection could not be established; distinct from a server-side failure."""


class MarketAuthenticationError(MarketDataError):
    pass


class MarketCredentialsRequiredError(MarketAuthenticationError):
    """Protected asset selected without external credentials."""


class MarketInvalidTokenError(MarketAuthenticationError):
    """HTTP 401: configured credentials were rejected."""


class MarketPlanAccessError(MarketAuthenticationError):
    """HTTP 403: the provider denied access under the current plan."""


class MarketRateLimitError(MarketDataError):
    pass


class AssetNotFoundError(MarketDataError):
    pass


@dataclass(frozen=True, slots=True)
class QuoteIssue:
    asset: Asset
    error: MarketDataError


@dataclass(frozen=True, slots=True)
class QuoteBatch:
    quotes: tuple[Quote, ...]
    issues: tuple[QuoteIssue, ...] = ()


class MarketDataProvider(ABC):
    """Replaceable market boundary with partial, batched quote availability."""

    def get_integration_status(self) -> MarketIntegrationStatus | None:
        """Optional safe diagnostics; providers without this capability return None."""
        return None

    def invalidate(self, asset: Asset | None = None) -> None:
        """Optional in-memory refresh hook; uncached providers need no action."""

    def refresh_context(self, explicit: bool) -> AbstractContextManager[None]:
        return nullcontext()

    def get_quote(self, asset: Asset) -> Quote:
        batch = self.get_quotes([asset])
        for quote in batch.quotes:
            if quote.asset == asset:
                return quote
        for issue in batch.issues:
            if issue.asset == asset:
                raise issue.error
        raise AssetNotFoundError("Ativo sem cotação disponível.")

    @abstractmethod
    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        """Fetch independent quotes efficiently, retaining per-asset failures."""

    @abstractmethod
    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        """Search the provider catalog; do not persist assets."""

    @abstractmethod
    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        """Return closing prices in chronological order, with source metadata."""
