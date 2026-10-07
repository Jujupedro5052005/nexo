from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary
from nexo.domain.models.market_data import Quote


@dataclass(frozen=True, slots=True)
class Indicator:
    key: str
    label: str
    value: Decimal | None
    unit: str
    formula: str
    origin: str
    reason: str = ""


def dividend_window(as_of: date) -> tuple[date, date]:
    try:
        previous = as_of.replace(year=as_of.year - 1)
    except ValueError:
        previous = as_of.replace(year=as_of.year - 1, day=28)
    return previous + timedelta(days=1), as_of


def annual_dividend(
    summary: DividendSummary | None, *, include_jcp: bool = False
) -> Decimal | None:
    if summary is None:
        return None
    events = [
        event
        for event in summary.events
        if (
            basis := event.ex_date
            if summary.date_basis == "ex_date"
            else event.payment_date
        )
        is not None
        and summary.start_date <= basis <= summary.end_date
        and event.verified is not False
        and (event.kind in {"DIVIDENDO", "CASH_DISTRIBUTION"} or include_jcp)
    ]
    with localcontext(
        financial_context((event.amount for event in events), count=len(events))
    ):
        return sum((event.amount for event in events), Decimal(0))


def fundamental_indicators(
    fundamentals: CompanyFundamentals | None,
    quote: Quote | None,
    dividend: Decimal | None,
) -> tuple[Indicator, ...]:
    f = fundamentals
    price = quote.price if quote is not None and quote.currency == "BRL" else None
    values = [price, dividend] + (
        [f.eps, f.bvps, f.revenue, f.ebitda, f.debt, f.cash] if f else []
    )
    with localcontext(financial_context(values)):
        pe = (
            price / f.eps
            if f and price is not None and f.eps is not None and f.eps > 0
            else None
        )
        pb = (
            price / f.bvps
            if f and price is not None and f.bvps is not None and f.bvps > 0
            else None
        )
        dy = (
            dividend / price
            if dividend is not None
            and dividend >= 0
            and price is not None
            and price > 0
            else None
        )
        margin = (
            f.ebitda / f.revenue
            if f and f.ebitda is not None and f.revenue is not None and f.revenue > 0
            else None
        )
        leverage = (
            (f.debt - f.cash) / f.ebitda
            if f
            and f.debt is not None
            and f.cash is not None
            and f.debt >= 0
            and f.cash >= 0
            and f.ebitda is not None
            and f.ebitda > 0
            else None
        )
    items = (
        (
            "eps",
            "LPA (12M)",
            f.eps if f else None,
            "money",
            "Lucro por ação 12M informado",
            "statistics.trailingEps (fallback earningsPerShare)",
        ),
        (
            "bvps",
            "VPA",
            f.bvps if f else None,
            "money",
            "Patrimônio líquido / ações; informado",
            "statistics.bookValue",
        ),
        ("pe", "P/L", pe, "multiple", "Preço BRL / LPA positivo", "Quote + statistics"),
        (
            "pb",
            "P/VP",
            pb,
            "multiple",
            "Preço BRL / VPA positivo",
            "Quote + statistics",
        ),
        (
            "dy",
            "DY da janela",
            dy,
            "ratio",
            "Proventos selecionados por ação na janela / preço BRL",
            "dividends.rate/paymentDate + Quote",
        ),
        (
            "roe",
            "ROE informado (12M)",
            f.roe if f else None,
            "ratio",
            "Lucro líquido 12M / patrimônio; base definida pelo provider",
            "financial-data.returnOnEquity",
        ),
        (
            "roa",
            "ROA informado (12M)",
            f.roa if f else None,
            "ratio",
            "Lucro líquido 12M / ativos; base definida pelo provider",
            "financial-data.returnOnAssets",
        ),
        (
            "net_margin",
            "Margem líquida informada",
            f.net_margin if f else None,
            "ratio",
            "Lucro líquido 12M / receita; informado",
            "financial-data.profitMargins",
        ),
        (
            "ebitda_margin",
            "Margem EBITDA calculada",
            margin,
            "ratio",
            "EBITDA 12M / receita 12M positiva",
            "financial-data.ebitda/totalRevenue",
        ),
        (
            "leverage",
            "Dívida líquida / EBITDA",
            leverage,
            "multiple",
            "(Dívida total − caixa) / EBITDA positivo",
            "financial-data.totalDebt/totalCash/ebitda",
        ),
    )
    result = tuple(
        Indicator(
            key,
            label,
            value,
            unit,
            formula,
            origin,
            "Dados insuficientes, moeda incompatível ou denominador não positivo."
            if value is None
            else "",
        )
        for key, label, value, unit, formula, origin in items
    )
    if f and f.source in {"bolsai", "CVM"}:
        from dataclasses import replace

        direct = {
            "pe": f.pe,
            "pb": f.pb,
            "ebitda_margin": f.ebitda_margin,
            "leverage": f.net_debt_ebitda,
        }
        result = tuple(
            replace(
                i,
                value=direct[i.key],
                origin=f"{f.source}.{i.key}",
                formula="Valor informado pelo provider",
                reason="" if direct[i.key] is not None else i.reason,
            )
            if i.key in direct and direct[i.key] is not None
            else replace(
                i,
                origin="Nexo calculations · " + f.source + " + Quote"
                if i.key in {"pe", "pb", "ebitda_margin", "leverage"}
                else f.source
                if i.key != "dy"
                else "Proventos + Quote",
            )
            for i in result
        )
        extra = (
            ("ev_ebitda", "EV/EBITDA", "multiple"),
            ("roic", "ROIC", "ratio"),
            ("gross_margin", "Margem bruta", "ratio"),
            ("debt_equity", "Dívida/patrimônio", "multiple"),
            ("current_ratio", "Liquidez corrente", "multiple"),
            ("market_cap", "Market Cap", "money"),
            ("revenue", "Receita", "money"),
            ("net_income", "Lucro líquido", "money"),
            ("equity", "Patrimônio líquido", "money"),
            ("debt", "Dívida", "money"),
            ("cash", "Caixa", "money"),
            ("total_assets", "Ativos", "money"),
            ("ebit", "EBIT", "money"),
            ("ebitda", "EBITDA", "money"),
        )
        result += tuple(
            Indicator(
                key,
                label,
                getattr(f, key),
                unit,
                "Valor informado pelo provider",
                f"{f.source}.{key}",
                "Campo indisponível" if getattr(f, key) is None else "",
            )
            for key, label, unit in extra
        )
    return result
