from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import cast

from nexo.application.assets.official_data import (
    GetOfficialCompanyData,
    OfficialCompanyData,
)
from nexo.calculations.indicators.fundamentals import (
    Indicator,
    annual_dividend,
    dividend_window,
    fundamental_indicators,
)
from nexo.calculations.indicators.official import cross_check
from nexo.calculations.risk.history import HistoricalRisk, historical_risk
from nexo.calculations.valuation.company import (
    SafetyMargin,
    bazin_price,
    graham_price,
    safety_margin,
)
from nexo.domain.interfaces.corporate_action_provider import CorporateActionProvider
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    MarketDataError,
    MarketDataProvider,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary
from nexo.domain.models.market_data import PriceHistory, Quote
from nexo.domain.models.official_data import CorporateAction


@dataclass(frozen=True, slots=True)
class ValuationEstimate:
    name: str
    price: Decimal | None
    margin: SafetyMargin | None
    reason: str
    currency: str = "BRL"


@dataclass(frozen=True, slots=True)
class AssetAnalysis:
    asset: Asset
    quote: Quote | None
    fundamentals: CompanyFundamentals | None
    dividends: DividendSummary | None
    history: PriceHistory | None
    indicators: tuple[Indicator, ...]
    annual_dividend: Decimal | None
    graham: ValuationEstimate
    bazin: ValuationEstimate
    risk: HistoricalRisk
    required_yield: Decimal | None
    include_jcp: bool
    issues: tuple[str, ...]
    official: OfficialCompanyData | None = None
    diagnostics: tuple[str, ...] = ()
    actions: tuple[CorporateAction, ...] = ()


class AnalyzeAsset:
    def __init__(
        self,
        market: MarketDataProvider,
        fundamentals: FundamentalDataProvider,
        *,
        today: Callable[[], date] | None = None,
        dividends: DividendDataProvider | None = None,
        official: GetOfficialCompanyData | None = None,
        actions: CorporateActionProvider | None = None,
    ) -> None:
        self._market, self._fundamentals = market, fundamentals
        self._dividends = dividends or cast(DividendDataProvider, fundamentals)
        self._official = official
        self._actions = actions
        self._today = today or (lambda: datetime.now(timezone.utc).date())

    def execute(
        self,
        asset: Asset,
        *,
        period: str = "1mo",
        required_yield: Decimal | None = None,
        include_jcp: bool = False,
        refresh: bool = False,
        include_actions: bool = False,
    ) -> AssetAnalysis:
        with self._market.refresh_context(refresh):
            return self._execute(
                asset,
                period=period,
                required_yield=required_yield,
                include_jcp=include_jcp,
                refresh=refresh,
                include_actions=include_actions,
            )

    def _execute(
        self,
        asset: Asset,
        *,
        period: str = "1mo",
        required_yield: Decimal | None = None,
        include_jcp: bool = False,
        refresh: bool = False,
        include_actions: bool = False,
    ) -> AssetAnalysis:
        if required_yield is not None:
            bazin_price(None, required_yield)  # Validate the premise before any I/O.
        if refresh:
            self._market.invalidate(asset)
            if self._official:
                self._official.invalidate(asset)
        start, end = dividend_window(self._today())
        issues: list[str] = []
        quote = None
        fundamentals = None
        dividends = None
        history = None
        try:
            quote = self._market.get_quote(asset)
        except MarketDataError as error:
            issues.append(f"Cotação: {error}")
        try:
            fundamentals = self._fundamentals.get_fundamentals(asset)
            issues.extend(fundamentals.issues)
        except MarketDataError as error:
            issues.append(f"Fundamentos: {error}")
        try:
            dividends = self._dividends.get_dividends(asset, start, end)
            issues.extend(dividends.limitations)
        except MarketDataError as error:
            issues.append(f"Proventos: {error}")
        try:
            history = self._market.get_history(asset, period)
        except MarketDataError as error:
            issues.append(f"Histórico: {error}")
        official = self._official.execute(asset) if self._official else None
        actions: tuple[CorporateAction, ...] = ()
        if include_actions and self._actions:
            try:
                actions = self._actions.get_actions(asset)
            except MarketDataError as error:
                issues.append(f"Splits: {error}")
        diagnostics = (
            cross_check(fundamentals, official.statements)
            if fundamentals and official
            else ()
        )
        annual = annual_dividend(dividends, include_jcp=include_jcp)
        graham = graham_price(
            fundamentals.eps if fundamentals else None,
            fundamentals.bvps if fundamentals else None,
        )
        bazin = (
            bazin_price(annual, required_yield) if required_yield is not None else None
        )
        current = quote.price if quote is not None and quote.currency == "BRL" else None

        def estimate(
            name: str, price: Decimal | None, missing: str
        ) -> ValuationEstimate:
            return ValuationEstimate(
                name,
                price,
                safety_margin(price, current),
                missing
                if price is None
                else "Cotação BRL indisponível para margem de segurança."
                if current is None
                else "",
            )

        return AssetAnalysis(
            asset,
            quote,
            fundamentals,
            dividends,
            history,
            fundamental_indicators(fundamentals, quote, annual),
            annual,
            estimate("Graham", graham, "LPA e VPA positivos são necessários."),
            estimate(
                "Bazin",
                bazin,
                "Informe yield requerido positivo; são necessários proventos positivos da janela.",
            ),
            historical_risk(history),
            required_yield,
            include_jcp,
            tuple(issues),
            official,
            diagnostics,
            actions,
        )
