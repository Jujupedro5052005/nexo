"""Conservative, identifiable accounts only; no TTM inference from raw statements."""

import unicodedata
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.fundamentals import CompanyFundamentals
from nexo.domain.models.official_data import OfficialFinancialStatement

ACCOUNTS = {
    "equity": ("BPP", "2.03", {"patrimonio liquido", "patrimonio liquido consolidado"}),
    "total_assets": ("BPA", "1", {"ativo total"}),
    "revenue": (
        "DRE",
        "3.01",
        {
            "receita de venda de bens e/ou servicos",
            "receita de venda de bens e servicos",
        },
    ),
    "net_income": (
        "DRE",
        "3.11",
        {"lucro/prejuizo consolidado do periodo", "lucro/prejuizo do periodo"},
    ),
}


def _name(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if not unicodedata.combining(c)
    ).strip()


def official_basics(rows: tuple[OfficialFinancialStatement, ...]) -> dict[str, Decimal]:
    if not rows:
        return {}
    latest = max(r.reference_date for r in rows)
    result = {}
    for field, (statement, account, names) in ACCOUNTS.items():
        matches = [
            r
            for r in rows
            if r.reference_date == latest
            and r.statement_type == statement
            and r.account_code == account
            and _name(r.account_name) in names
        ]
        if len(matches) == 1:
            result[field] = matches[0].value
    return result


def cross_check(
    f: CompanyFundamentals, rows: tuple[OfficialFinancialStatement, ...]
) -> tuple[str, ...]:
    rows = tuple(r for r in rows if r.reference_date == f.reference_date)
    basics = official_basics(rows)
    messages = []
    for field, official in basics.items():
        # bolsai flows are TTM; only compare against an annual DFP with annual period.
        if field in {"revenue", "net_income"} and not any(
            r.report_type == "DFP"
            and r.period_start
            and r.period_end
            and (r.period_end - r.period_start).days >= 364
            for r in rows
            if r.statement_type == "DRE"
        ):
            continue
        aggregated = getattr(f, field)
        if aggregated is not None and aggregated != official:
            with localcontext(financial_context([aggregated, official])):
                difference = aggregated - official
            messages.append(
                f"{field}: dados agregados e CVM apresentam diferença de BRL {difference} (mesma referência)."
            )
    return tuple(messages)
