"""Capability-specific routing; source values are never averaged or merged."""

from collections.abc import Iterable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import fields
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import partial
from typing import Any

from nexo.domain.interfaces.corporate_action_provider import CorporateActionProvider
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    MarketDataError,
    MarketDataProvider,
    MarketDataUnavailableError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.interfaces.official_data_provider import (
    OfficialFinancialStatementProvider,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.domain.models.market_integration import MarketIntegrationStatus
from nexo.domain.models.official_data import CorporateAction
from nexo.infrastructure.market_data.policy import ProviderPolicy, explicit_refresh


class RoutedMarketDataProvider(MarketDataProvider):
    def __init__(
        self,
        brapi: MarketDataProvider,
        bolsai: MarketDataProvider,
        yahoo: Any,
        policy: ProviderPolicy,
    ) -> None:
        self.brapi, self.bolsai, self.yahoo, self.policy = brapi, bolsai, yahoo, policy

    def get_integration_status(self) -> MarketIntegrationStatus | None:
        return self.brapi.get_integration_status()

    def invalidate(self, asset: Asset | None = None) -> None:
        self.policy.invalidate(asset)

    def refresh_context(self, explicit: bool) -> AbstractContextManager[None]:
        return explicit_refresh() if explicit else nullcontext()

    def get_quote(self, asset: Asset) -> Quote:
        with self.policy.coalesce_route("quote", (asset,)):
            return self._quote(asset)

    def _quote(self, asset: Asset) -> Quote:
        for name in ("brapi", "bolsai"):
            cached = self.policy.cached(name, "quote", (asset,))
            if cached:
                return cached
        primary_error: MarketDataError | None = None
        for name, provider in (("brapi", self.brapi), ("bolsai", self.bolsai)):
            try:
                return self.policy.call(
                    name, "quote", (asset,), partial(provider.get_quote, asset)
                )
            except MarketDataError as error:
                if name == "brapi":
                    primary_error = error
                else:
                    assert primary_error is not None
                    # Keep the primary failure category, so missing fallback
                    # credentials cannot disguise a local budget/plan failure.
                    raise type(primary_error)(
                        f"brapi (prioritária): {primary_error} | bolsai (fallback): {error}"
                    ) from None
        raise MarketDataUnavailableError("Nenhuma fonte de cotação disponível.")

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        quotes, issues = [], []
        for asset in dict.fromkeys(assets):
            try:
                quotes.append(self.get_quote(asset))
            except MarketDataError as error:
                issues.append(QuoteIssue(asset, error))
        return QuoteBatch(tuple(quotes), tuple(issues))

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        with self.policy.coalesce_route("search", (query.strip().upper(),)):
            return self._search(query)

    def _search(self, query: str) -> tuple[AssetSearchResult, ...]:
        query = query.strip().upper()
        for name in ("brapi", "bolsai"):
            cached = self.policy.cached(name, "search", (query,))
            if cached:
                return cached
        for name, provider in (("brapi", self.brapi), ("bolsai", self.bolsai)):
            try:
                result = self.policy.call(
                    name, "search", (query,), partial(provider.search_assets, query)
                )
                if result:
                    return result
            except MarketDataError:
                if name == "bolsai":
                    raise
        return ()

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        with self.policy.coalesce_route("history", (asset, period)):
            return self._history(asset, period)

    def _history(self, asset: Asset, period: str) -> PriceHistory:
        if period not in {"1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"}:
            raise MarketDataUnavailableError("Período não suportado.")
        for name in (
            ("brapi", "Yahoo Finance")
            if period in {"1mo", "3mo"}
            else ("Yahoo Finance",)
        ):
            cached = self.policy.cached(name, "history", (asset, period))
            if cached is not None and cached.points:
                return cached
        if period in {"1mo", "3mo"}:
            try:
                result = self.policy.call(
                    "brapi",
                    "history",
                    (asset, period),
                    lambda: self.brapi.get_history(asset, period),
                )
                if result.points:
                    return result
            except MarketDataError:
                pass
        return self.policy.call(
            "Yahoo Finance",
            "history",
            (asset, period),
            lambda: self.yahoo.get_history(asset, period),
        )


class RoutedDividendDataProvider(DividendDataProvider):
    def __init__(
        self,
        yahoo: DividendDataProvider,
        brapi: DividendDataProvider,
        policy: ProviderPolicy,
        *,
        brapi_enabled: bool = False,
    ) -> None:
        self.yahoo, self.brapi, self.policy, self.brapi_enabled = (
            yahoo,
            brapi,
            policy,
            brapi_enabled,
        )

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        with self.policy.coalesce_route("dividends", (asset, start_date, end_date)):
            return self._dividends(asset, start_date, end_date)

    def _dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        key = (asset, start_date, end_date)
        for name in (
            ("Yahoo Finance", "brapi") if self.brapi_enabled else ("Yahoo Finance",)
        ):
            cached = self.policy.cached(name, "dividends", key)
            if cached is not None:
                return cached
        try:
            return self.policy.call(
                "Yahoo Finance",
                "dividends",
                key,
                lambda: self.yahoo.get_dividends(asset, start_date, end_date),
            )
        except MarketDataError:
            if not self.brapi_enabled:
                raise
        return self.policy.call(
            "brapi",
            "dividends",
            key,
            lambda: self.brapi.get_dividends(asset, start_date, end_date),
        )


class RoutedFundamentalDataProvider(FundamentalDataProvider):
    def __init__(
        self,
        bolsai: FundamentalDataProvider,
        cvm: OfficialFinancialStatementProvider,
        policy: ProviderPolicy,
        *,
        brapi: FundamentalDataProvider | None = None,
    ) -> None:
        self.bolsai, self.cvm, self.policy = bolsai, cvm, policy
        self.brapi = brapi

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        with self.policy.coalesce_route("fundamentals", (asset,)):
            return self._fundamentals(asset)

    def _fundamentals(self, asset: Asset) -> CompanyFundamentals:
        providers: list[tuple[str, FundamentalDataProvider]] = []
        if self.brapi is not None:
            providers.append(("brapi", self.brapi))
        providers.append(("bolsai", self.bolsai))
        for name in [*(name for name, _ in providers), "CVM"]:
            cached = self.policy.cached(name, "fundamentals", (asset,))
            if cached is not None and (name == "CVM" or self._has_inputs(cached)):
                return cached
        for name, provider in providers:
            try:
                result = self.policy.call(
                    name,
                    "fundamentals",
                    (asset,),
                    partial(provider.get_fundamentals, asset),
                )
                if self._has_inputs(result):
                    return result
            except MarketDataError:
                pass

        def official() -> CompanyFundamentals:
            rows = self.cvm.get_statements(asset)
            from nexo.calculations.indicators.official import official_basics

            values = official_basics(rows)
            return CompanyFundamentals(
                asset,
                datetime.now(timezone.utc),
                source="CVM",
                reference_date=max(r.reference_date for r in rows),
                issues=(
                    "CVM · dados oficiais/raw; não são indicadores TTM agregados.",
                ),
                equity=values.get("equity"),
                revenue=values.get("revenue"),
                net_income=values.get("net_income"),
                total_assets=values.get("total_assets"),
            )

        return self.policy.call("CVM", "fundamentals", (asset,), official)

    @staticmethod
    def _has_inputs(snapshot: CompanyFundamentals) -> bool:
        return any(
            isinstance(getattr(snapshot, field.name), Decimal)
            for field in fields(snapshot)
        )


class RoutedCorporateActions(CorporateActionProvider):
    def __init__(
        self,
        yahoo: Any,
        bolsai: Any,
        policy: ProviderPolicy,
        *,
        bolsai_enabled: bool = False,
    ) -> None:
        self.yahoo, self.bolsai, self.policy, self.bolsai_enabled = (
            yahoo,
            bolsai,
            policy,
            bolsai_enabled,
        )

    def get_actions(self, asset: Asset) -> tuple[CorporateAction, ...]:
        with self.policy.coalesce_route("actions", (asset,)):
            return self._actions(asset)

    def _actions(self, asset: Asset) -> tuple[CorporateAction, ...]:
        for name in (
            ("Yahoo Finance", "bolsai") if self.bolsai_enabled else ("Yahoo Finance",)
        ):
            cached = self.policy.cached(name, "actions", (asset,))
            if cached is not None:
                return cached
        try:
            return self.policy.call(
                "Yahoo Finance",
                "actions",
                (asset,),
                lambda: self.yahoo.get_actions(asset),
            )
        except MarketDataError:
            if not self.bolsai_enabled:
                raise
        return self.policy.call(
            "bolsai", "actions", (asset,), lambda: self.bolsai.get_actions(asset)
        )
