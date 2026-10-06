from collections.abc import Sequence
from decimal import Context, Decimal, localcontext

from PySide6.QtWidgets import QTableWidgetItem

from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.reconstruction import ReconstructionResult
from nexo.ui.components.common import DataTable


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def money_text(value: Decimal) -> str:
    return "R$ " + format(value, ",.2f").replace(",", "_").replace(".", ",").replace(
        "_", "."
    )


def replace_rows(table: DataTable, rows: Sequence[tuple[str, ...]]) -> None:
    table.setRowCount(len(rows))
    for row, values in enumerate(rows):
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))
    table.setMinimumHeight(min(420, 54 + 42 * len(rows)))


def position_rows(result: ReconstructionResult) -> list[tuple[str, ...]]:
    return [
        (
            p.asset.symbol,
            decimal_text(p.quantity),
            money_text(p.average_cost),
            money_text(p.cost_basis),
            money_text(p.realized_profit_loss),
        )
        for p in result.positions
    ]


MARKET_HEADERS = (
    "ATIVO",
    "QUANTIDADE",
    "CUSTO MÉDIO",
    "CUSTO TOTAL",
    "REALIZADO",
    "PREÇO ATUAL",
    "VALOR ATUAL",
    "NÃO REALIZADO",
    "RETORNO ABERTO",
)


def currency_text(value: Decimal | None, currency: str = "BRL") -> str:
    if value is None:
        return "—"
    return (
        money_text(value) if currency == "BRL" else f"{currency} {decimal_text(value)}"
    )


def percent_text(ratio: Decimal | None) -> str:
    if ratio is None:
        return "—"
    with localcontext(Context(prec=max(50, len(ratio.as_tuple().digits) + 5))):
        return format(ratio * Decimal(100), ".2f").replace(".", ",") + "%"


def valued_rows(valuation: PortfolioValuation) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for item in valuation.positions:
        p, q = item.position, item.quote
        rows.append(
            (
                p.asset.symbol,
                decimal_text(p.quantity),
                money_text(p.average_cost),
                money_text(p.cost_basis),
                money_text(p.realized_profit_loss),
                currency_text(q.price, q.currency) if q else "—",
                currency_text(item.market_value, q.currency) if q else "—",
                currency_text(item.unrealized_profit_loss),
                percent_text(item.unrealized_return),
            )
        )
    return rows


def market_status(valuation: PortfolioValuation) -> str:
    quotes = [p.quote for p in valuation.positions if p.quote is not None]
    if not valuation.positions:
        return "Sem posições abertas; nenhuma cotação necessária."
    if not quotes:
        reasons = dict.fromkeys(p.unavailable_reason for p in valuation.positions)
        return "Mercado indisponível. " + " ".join(reasons)
    updated = min(q.retrieved_at for q in quotes).isoformat(timespec="seconds")
    market_times = [q.market_time for q in quotes if q.market_time is not None]
    timestamp = (
        min(market_times).isoformat(timespec="seconds")
        if market_times
        else "não informado"
    )
    return (
        f"Origem: {', '.join(sorted({q.source for q in quotes}))} • Consultado: {updated} • Cotação mais antiga: {timestamp}"
        + (
            " • Valuation incompleto: cotação ausente ou moeda sem conversão."
            if not valuation.complete
            else ""
        )
    )


def apply_valuation(table: DataTable, valuation: PortfolioValuation) -> None:
    replace_rows(table, valued_rows(valuation))
    for row, position in enumerate(valuation.positions):
        quote = position.quote
        detail = position.unavailable_reason or (
            f"{quote.source}; consultado {quote.retrieved_at.isoformat()}; mercado {quote.market_time.isoformat() if quote.market_time else 'não informado'}"
            if quote
            else "Sem cotação"
        )
        for column in range(5, table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                item.setToolTip(detail)
