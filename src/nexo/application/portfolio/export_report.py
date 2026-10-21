import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Protocol

from nexo.application.financial_planning.manage_finances import ManageFinances
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.domain.interfaces.portfolio_event_repository import PortfolioEventRepository


class ReportWriter(Protocol):
    def write(self, path: str, content: str) -> None: ...


class ExportReport:
    def __init__(
        self,
        transactions: ListTransactions,
        positions: LoadPortfolioPositions,
        finances: ManageFinances,
        writer: ReportWriter,
        events: PortfolioEventRepository | None = None,
    ) -> None:
        self.events = events
        self.transactions, self.positions, self.finances, self.writer = (
            transactions,
            positions,
            finances,
            writer,
        )

    def execute(self, kind: str, portfolio_id: int | None, path: str) -> int:
        headers: tuple[str, ...]
        rows: list[tuple[str, ...]] = []
        if kind in {"positions", "transactions", "events"} and portfolio_id is None:
            raise ValueError("Selecione uma carteira.")
        if kind == "positions":
            assert portfolio_id is not None
            headers = (
                "carteira_id",
                "ativo",
                "quantidade",
                "preco_medio_brl",
                "custo_brl",
                "realizado_brl",
            )
            result = self.positions.execute(portfolio_id)
            rows = [
                (
                    str(portfolio_id),
                    p.asset.symbol,
                    str(p.quantity),
                    str(p.average_cost),
                    str(p.cost_basis),
                    str(p.realized_profit_loss),
                )
                for p in result.positions + result.closed_positions
            ]
        elif kind == "transactions":
            assert portfolio_id is not None
            headers = (
                "id",
                "carteira_id",
                "data",
                "tipo",
                "ativo",
                "quantidade",
                "preco_brl",
                "taxas_brl",
                "bruto_brl",
                "liquido_brl",
            )
            rows = [
                (
                    str(t.id),
                    str(t.portfolio_id),
                    t.occurred_at.isoformat(),
                    t.transaction_type.value,
                    t.asset.symbol,
                    str(t.quantity),
                    str(t.unit_price),
                    str(t.fees),
                    str(t.amounts()[0]),
                    str(t.amounts()[1]),
                )
                for t in self.transactions.execute(portfolio_id)
            ]
        elif kind == "events":
            if self.events is None or portfolio_id is None:
                raise ValueError("Livro de caixa indisponível.")
            headers = (
                "id",
                "carteira_id",
                "data",
                "tipo",
                "ativo",
                "bruto_brl",
                "retencao_brl",
                "efeito_caixa_brl",
                "fluxo_externo_brl",
                "razao",
                "observacao",
            )
            rows = [
                (
                    str(e.id),
                    str(e.portfolio_id),
                    e.occurred_at.isoformat(),
                    e.kind.value,
                    e.asset.symbol if e.asset else "",
                    str(e.amount),
                    str(e.withholding),
                    str(e.cash_effect),
                    str(e.external_flow),
                    str(e.ratio) if e.ratio is not None else "",
                    e.note,
                )
                for e in self.events.list_events(portfolio_id)
            ]
        elif kind == "planning":
            headers = ("descricao", "tipo", "mes", "valor_brl")
            rows = [
                (e.name, e.kind, e.month.isoformat(), str(e.amount))
                for e in self.finances.budget_entries()
            ]
        elif kind == "goals":
            headers = ("meta", "objetivo_brl", "acumulado_brl", "prazo")
            rows = [
                (g.name, str(g.target), str(g.current), g.deadline.isoformat())
                for g in self.finances.goals()
            ]
        else:
            raise ValueError("Tipo de relatório não suportado.")
        stream = StringIO(newline="")
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(headers)

        # Spreadsheet programs must not interpret user-provided names as formulas.
        def spreadsheet_cell(cell: str) -> str:
            if cell.lstrip().startswith(("=", "+", "-", "@")):
                try:
                    if not Decimal(cell).is_finite():
                        return "'" + cell
                except InvalidOperation:
                    return "'" + cell
            return cell

        writer.writerows(tuple(spreadsheet_cell(cell) for cell in row) for row in rows)
        self.writer.write(path, stream.getvalue())
        return len(rows)
