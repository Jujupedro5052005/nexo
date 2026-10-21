"""Capability-specific routing; source values are never averaged or merged."""

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager, nullcontext
from contextvars import copy_context
from dataclasses import fields, replace
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
        return (
            self.yahoo.get_integration_status()
            if hasattr(self.yahoo, "get_integration_status")
            else self.brapi.get_integration_status()
        )

    def invalidate(self, asset: Asset | None = None) -> None:
        self.policy.invalidate(asset)
        if hasattr(self.yahoo, "invalidate"):
            self.yahoo.invalidate(asset)

    def refresh_context(self, explicit: bool) -> AbstractContextManager[None]:
        return explicit_refresh() if explicit else nullcontext()

    def get_quote(self, asset: Asset) -> Quote:
        with self.policy.coalesce_route("quote", (asset,)):
            return self._quote(asset)

    def _quote(self, asset: Asset, *, fallback_only: bool = False) -> Quote:
        errors = []
        providers = (
            ("Yahoo Finance", self.yahoo),
            ("brapi", self.brapi),
            ("bolsai", self.bolsai),
        )
        for name, provider in providers[1:] if fallback_only else providers:
            if not hasattr(provider, "get_quote"):
                continue
            try:
                return self.policy.call(
                    name, "quote", (asset,), partial(provider.get_quote, asset)
                )
            except MarketDataError as error:
                errors.append((name, error))
        if errors:
            raise type(errors[0][1])(
                " | ".join(f"{name}: {error}" for name, error in errors)
            )
        raise MarketDataUnavailableError("Nenhuma fonte de cotação disponível.")

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        requested = tuple(dict.fromkeys(assets))
        if not requested:
            return QuoteBatch(())
        # Serialize equivalent batches, while preserving explicit/budget and
        # cancellation context in bounded fallback workers.
        with self.policy.coalesce_route("quote_batch", requested):
            quotes = {
                a: q
                for a in requested
                if (q := self.policy.cached("Yahoo Finance", "quote", (a,))) is not None
            }
            for asset in requested:
                if asset not in quotes and self.policy.recent_failure(
                    "Yahoo Finance", "quote", (asset,)
                ):
                    for provider in ("brapi", "bolsai"):
                        cached = self.policy.cached(provider, "quote", (asset,))
                        if cached is not None:
                            quotes[asset] = cached
                            break
            missing = tuple(a for a in requested if a not in quotes)
            primary_errors: dict[Asset, MarketDataError] = {}
            if missing and hasattr(self.yahoo, "get_quotes"):
                try:
                    batch = self.policy.call(
                        "Yahoo Finance",
                        "quote_batch",
                        missing,
                        lambda: self.yahoo.get_quotes(missing),
                    )
                    for quote in batch.quotes:
                        if quote.asset in missing:
                            quotes[quote.asset] = quote
                    primary_errors = {
                        issue.asset: issue.error for issue in batch.issues
                    }
                except MarketDataError as error:
                    primary_errors = dict.fromkeys(missing, error)
            remaining = tuple(a for a in missing if a not in quotes)

            def complement(asset: Asset) -> Quote | QuoteIssue:
                try:
                    # For adapters without a batch capability retain ordinary routing.
                    return self._quote(
                        asset, fallback_only=hasattr(self.yahoo, "get_quotes")
                    )
                except MarketDataError as error:
                    original = primary_errors.get(asset)
                    return QuoteIssue(
                        asset,
                        MarketDataUnavailableError(
                            f"Yahoo Finance: {original} | Complementos: {error}"
                        )
                        if original
                        else error,
                    )

            if remaining:
                with ThreadPoolExecutor(max_workers=min(4, len(remaining))) as pool:
                    futures = [
                        pool.submit(copy_context().run, complement, a)
                        for a in remaining
                    ]
                    results = [f.result() for f in futures]
                issues = tuple(r for r in results if isinstance(r, QuoteIssue))
                quotes.update((r.asset, r) for r in results if isinstance(r, Quote))
            else:
                issues = ()
            return QuoteBatch(
                tuple(quotes[a] for a in requested if a in quotes), issues
            )

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        with self.policy.coalesce_route("search", (query.strip().upper(),)):
            return self._search(query)

    def _search(self, query: str) -> tuple[AssetSearchResult, ...]:
        query = query.strip().upper()
        for name, provider in (
            ("Yahoo Finance", self.yahoo),
            ("brapi", self.brapi),
            ("bolsai", self.bolsai),
        ):
            if not hasattr(provider, "search_assets"):
                continue
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
        try:
            result = self.policy.call(
                "Yahoo Finance",
                "history",
                (asset, period),
                lambda: self.yahoo.get_history(asset, period),
            )
            if result.points:
                return result
        except MarketDataError:
            pass
        return self.policy.call(
            "brapi",
            "history",
            (asset, period),
            lambda: self.brapi.get_history(asset, period),
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
        yahoo: FundamentalDataProvider | None = None,
    ) -> None:
        self.bolsai, self.cvm, self.policy = bolsai, cvm, policy
        self.brapi = brapi
        self.yahoo = yahoo

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        with self.policy.coalesce_route("fundamentals", (asset,)):
            return self._fundamentals(asset)

    def _fundamentals(self, asset: Asset) -> CompanyFundamentals:
        providers: list[tuple[str, FundamentalDataProvider]] = []
        if self.yahoo is not None:
            providers.append(("Yahoo Finance", self.yahoo))
        if self.brapi is not None:
            providers.append(("brapi", self.brapi))
        providers.append(("bolsai", self.bolsai))
        preferred: CompanyFundamentals | None = None
        for name, provider in providers:
            try:
                result = self.policy.call(
                    name,
                    "fundamentals",
                    (asset,),
                    partial(provider.get_fundamentals, asset),
                )
            except MarketDataError:
                continue
            if not self._has_inputs(result):
                continue
            if preferred is None:
                preferred = result
            elif (
                preferred.reference_date is not None
                and preferred.reference_date == result.reference_date
                and preferred.currency == result.currency
            ):
                # Supplement only missing fields with an aligned accounting reference.
                # Never replace Yahoo values or silently combine different quarters.
                missing = {
                    field.name: getattr(result, field.name)
                    for field in fields(result)
                    if getattr(preferred, field.name) is None
                    and isinstance(getattr(result, field.name), Decimal)
                }
                preferred = replace(
                    preferred,
                    **missing,
                    field_sources=preferred.field_sources
                    + tuple((key, result.source) for key in missing),
                )
            if preferred.eps is not None and preferred.bvps is not None:
                return preferred
        if preferred is not None:
            return preferred

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
