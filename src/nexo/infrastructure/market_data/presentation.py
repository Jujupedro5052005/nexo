"""Explicit fictional data for presentation mode, never a live-provider fallback."""

from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from nexo.demo_dataset import ENTRY_PRICES
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.market_data_provider import (
    AssetNotFoundError,
    MarketDataProvider,
    QuoteBatch,
    QuoteIssue,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import (
    CashDividend,
    CompanyFundamentals,
    DividendSummary,
)
from nexo.domain.models.market_data import (
    AssetSearchResult,
    HistoricalPrice,
    PriceHistory,
    Quote,
)

SOURCE = "Apresentação · dados fictícios, sem valor de mercado"


class PresentationMarketData(
    MarketDataProvider, FundamentalDataProvider, DividendDataProvider
):
    def __init__(self) -> None:
        self.as_of = datetime.now(timezone.utc).replace(microsecond=0)

    @staticmethod
    def _price(asset: Asset) -> Decimal:
        if asset.symbol not in ENTRY_PRICES:
            raise AssetNotFoundError(
                "Ativo fora do catálogo de apresentação. Use seu ambiente para mercado real."
            )
        index = list(ENTRY_PRICES).index(asset.symbol)
        factor = (Decimal("1.08"), Decimal("0.94"), Decimal("1.16"))[index % 3]
        return (Decimal(ENTRY_PRICES[asset.symbol][-1]) * factor).quantize(
            Decimal(".01")
        )

    def get_quotes(self, assets: Iterable[Asset]) -> QuoteBatch:
        quotes, issues = [], []
        for asset in assets:
            try:
                price = self._price(asset)
            except AssetNotFoundError as error:
                issues.append(QuoteIssue(asset, error))
                continue
            quotes.append(
                Quote(
                    asset,
                    price,
                    "BRL",
                    asset.symbol,
                    self.as_of,
                    market_time=self.as_of,
                    source=SOURCE,
                    price_kind="illustrative",
                    previous_close=price - Decimal(".30"),
                    change=Decimal(".30"),
                    change_percent=Decimal(".30") / (price - Decimal(".30")) * 100,
                    open=price - Decimal(".20"),
                    day_high=price + Decimal(".50"),
                    day_low=price - Decimal(".50"),
                    volume=1000000,
                )
            )
        return QuoteBatch(tuple(quotes), tuple(issues))

    def search_assets(self, query: str) -> tuple[AssetSearchResult, ...]:
        return tuple(
            AssetSearchResult(Asset(s), s, "BRL", source=SOURCE)
            for s in ENTRY_PRICES
            if query.strip().upper() in s
        )

    def get_history(self, asset: Asset, period: str) -> PriceHistory:
        price = self._price(asset)
        days = {"1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "2y": 732, "5y": 1830}.get(
            period, 1830
        )
        points = []
        for offset in range(days, -1, -1):
            at = self.as_of - timedelta(days=offset)
            # A reproducible path with gains, drawdowns and the exact terminal quote.
            wave = Decimal((offset % 21) - (offset % 7)) / 1000
            close = (price * (1 - Decimal(offset) / 10000 + wave)).quantize(
                Decimal(".01")
            )
            points.append(HistoricalPrice(at, close, volume=1000000))
        return PriceHistory(
            asset, tuple(points), period, self.as_of, SOURCE, split_adjusted=False
        )

    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        price = self._price(asset)
        if asset.symbol in {"BOVA11", "IVVB11"}:
            return CompanyFundamentals(
                asset,
                self.as_of,
                source=SOURCE,
                issues=("ETF: fundamentos corporativos não se aplicam.",),
            )
        index = list(ENTRY_PRICES).index(asset.symbol)
        pe, pb = Decimal(6 + index % 5 * 3), Decimal("1.2") + Decimal(index % 4) / 2
        eps, bvps = price / pe, price / pb
        equity = bvps * 1000000000
        income = eps * 1000000000
        return CompanyFundamentals(
            asset,
            self.as_of,
            eps=eps,
            bvps=bvps,
            pe=pe,
            pb=pb,
            roe=income / equity,
            roa=income / (equity * 2),
            roic=Decimal(".14"),
            revenue=income * 5,
            net_income=income,
            net_margin=Decimal(".20"),
            equity=equity,
            total_assets=equity * 2,
            debt=equity / 2,
            cash=equity / 10,
            ebitda=income * 2,
            ebit=income * Decimal("1.5"),
            market_cap=price * 1000000000,
            current_ratio=Decimal("1.6"),
            debt_equity=Decimal(".5"),
            gross_margin=Decimal(".4"),
            ebitda_margin=Decimal(".4"),
            net_debt_ebitda=(equity * Decimal(".4")) / (income * 2),
            ev_ebitda=(price * 1000000000 + equity * Decimal(".4")) / (income * 2),
            reference_date=self.as_of.date(),
            source=SOURCE,
            issues=("Cenário didático; não representa demonstrações da companhia.",),
        )

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        price = self._price(asset)
        events = []
        if asset.symbol not in {"BOVA11", "IVVB11"}:
            for offset in range(90, (end_date - start_date).days + 1, 90):
                at = end_date - timedelta(days=offset)
                events.append(
                    CashDividend(
                        at,
                        (price * Decimal(".015")).quantize(Decimal(".01")),
                        "DIVIDENDO",
                        False,
                        asset=asset,
                        source=SOURCE,
                    )
                )
        return DividendSummary(
            asset,
            tuple(sorted(events, key=lambda e: e.payment_date or date.min)),
            start_date,
            end_date,
            self.as_of,
            source=SOURCE,
            limitations=("Eventos ilustrativos, não verificados no mercado.",),
        )
