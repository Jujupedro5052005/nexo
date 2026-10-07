from pathlib import Path

from nexo.application.assets.official_data import GetOfficialCompanyData
from nexo.domain.models.provider_health import ProviderHealth
from nexo.infrastructure.market_data.adapters.bolsai import BolsaiProvider
from nexo.infrastructure.market_data.adapters.brapi import BrapiMarketDataProvider
from nexo.infrastructure.market_data.adapters.cvm import (
    CompanyIdentityCache,
    CvmOfficialProvider,
)
from nexo.infrastructure.market_data.adapters.yahoo import YahooFinanceProvider
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.infrastructure.market_data.policy import ProviderPolicy, ProviderUsage
from nexo.infrastructure.market_data.routing import (
    RoutedCorporateActions,
    RoutedDividendDataProvider,
    RoutedFundamentalDataProvider,
    RoutedMarketDataProvider,
)


class ProviderServices:
    """Composition/lifecycle only; consumers receive separate capability contracts."""

    def __init__(self, settings: MarketSettings, data_dir: Path) -> None:
        self.settings = settings
        self.usage = ProviderUsage(
            data_dir / "provider_usage.json",
            {
                "brapi": settings.brapi_budget,
                "bolsai": settings.bolsai_budget,
                "Yahoo Finance": settings.yahoo_budget,
                "CVM": settings.cvm_budget,
            },
        )
        self.policy = ProviderPolicy(self.usage)
        self.brapi = BrapiMarketDataProvider(settings, usage=self.usage)
        self.bolsai = BolsaiProvider(settings, self.policy)
        self.yahoo = YahooFinanceProvider(self.usage)
        identities = CompanyIdentityCache(
            data_dir / "cache/official/identities", self.bolsai.get_company_identity
        )
        self.cvm = CvmOfficialProvider(
            self.policy, identities.resolve, data_dir / "cache/official/cvm"
        )
        self.market = RoutedMarketDataProvider(
            self.brapi, self.bolsai, self.yahoo, self.policy
        )
        self.fundamentals = RoutedFundamentalDataProvider(
            self.bolsai, self.cvm, self.policy, brapi=self.brapi
        )
        self.dividends = RoutedDividendDataProvider(
            self.yahoo,
            self.brapi,
            self.policy,
            brapi_enabled=settings.brapi_dividends_enabled,
        )
        self.actions = RoutedCorporateActions(
            self.yahoo,
            self.bolsai,
            self.policy,
            bolsai_enabled=settings.bolsai_actions_enabled,
        )
        self.official = GetOfficialCompanyData(self.cvm, self.cvm)

    def health(self) -> tuple[ProviderHealth, ...]:
        return (
            self.policy.health(
                "brapi",
                bool(self.settings.token),
                "market data/fundamentals primary · sandbox público sem chave",
            ),
            self.policy.health(
                "bolsai",
                bool(self.settings.bolsai_api_key),
                "fundamentals/quote EOD fallback · company metadata",
            ),
            self.policy.health(
                "Yahoo Finance", True, "fallback · dividends/history/actions"
            ),
            self.policy.health(
                "CVM",
                True,
                "fonte oficial · cadastro/DFP/ITR",
                self.cvm.cache_updates(),
            ),
        )

    def close(self) -> None:
        self.brapi.close()
        self.bolsai.close()
        self.cvm.close()
