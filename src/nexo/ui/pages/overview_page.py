from datetime import datetime, timezone
from decimal import Decimal

from PySide6.QtCharts import QChartView
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from nexo.application.portfolio.account import AccountSnapshot
from nexo.application.portfolio.dashboard import ledger_timeline
from nexo.application.portfolio.financial_summary import FinancialSummary
from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import ReconstructionResult
from nexo.ui.components.charts import bar_chart, capital_timeline_chart
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.components.concentration_panel import ConcentrationPanel
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.components.responsive_pair import ResponsivePair
from nexo.ui.financial_formatting import (
    MARKET_HEADERS,
    apply_valuation,
    currency_text,
    market_status,
    money_text,
    percent_text,
    position_rows,
    replace_rows,
)


class OverviewPage(PageContent):
    """Decision dashboard built from the selected ledger and available quotes."""

    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("overview")
        self.page_layout.addWidget(
            Badge("Seu panorama • dados reais da carteira selecionada")
        )
        self.context_label = QLabel("Selecione uma carteira para começar.")
        self.page_layout.addWidget(self.context_label)
        self.metrics: dict[str, MetricCard] = {}
        row = QHBoxLayout()
        for key, title, detail in (
            (
                "market",
                "VALOR DAS POSIÇÕES",
                "Quantidade × cotação de cada ativo. BRL, sem caixa. Agregado indisponível se faltar cotação.",
            ),
            (
                "unrealized",
                "RESULTADO EM ABERTO",
                "Valor atual − custo das posições abertas. Oscila com o preço; não inclui proventos ou impostos.",
            ),
            (
                "total",
                "RESULTADO TOTAL",
                "Resultado realizado nas vendas + resultado em aberto. Não inclui caixa ou proventos não registrados.",
            ),
            (
                "return",
                "RETORNO SOBRE CUSTO",
                "Resultado em aberto / custo aberto. Fotografia atual, sem considerar a duração dos investimentos.",
            ),
        ):
            short_detail = {
                "market": "Posições abertas • BRL • sem caixa",
                "unrealized": "Valor atual menos custo aberto",
                "total": "Realizado + resultado em aberto",
                "return": "Fotografia das posições abertas",
            }[key]
            metric = MetricCard(title, "—", short_detail, tooltip=detail)
            if key == "market":
                metric.setProperty("highlight", True)
            self.metrics[key] = metric
            row.addWidget(metric, 1)
        self.page_layout.addLayout(row)
        local = QHBoxLayout()
        for key, title in (
            ("portfolios", "CARTEIRAS"),
            ("positions", "ATIVOS EM CARTEIRA"),
            ("cost", "CAPITAL A CUSTO"),
            ("realized", "RESULTADO DAS VENDAS"),
            ("transactions", "OPERAÇÕES"),
        ):
            metric = MetricCard(
                title, "—", "Calculado do histórico local; não depende de APIs."
            )
            self.metrics[key] = metric
            local.addWidget(metric, 1)
        self.page_layout.addLayout(local)
        self.evolution_card = SectionCard("Sua trajetória • capital a custo")
        self.timeline_note = QLabel(
            "Registre compras e vendas para construir sua trajetória."
        )
        self.timeline_note.setWordWrap(True)
        self.timeline_note.setToolTip(
            "Custo das posições ainda abertas ao final de cada mês com operações. Vendas reduzem o custo; diferenças não representam rentabilidade. Meses sem operações não geram um novo ponto. Não é patrimônio histórico a mercado."
        )
        self.evolution_card.content.addWidget(self.timeline_note)
        self.timeline_chart: QChartView | None = None
        self.insights_card = SectionCard("Radar da carteira")
        self.insights_label = QLabel(
            "Atualize o mercado para identificar concentração e resultados."
        )
        self.insights_label.setWordWrap(True)
        self.insights_card.content.addWidget(self.insights_label)
        self.insights_card.content.addStretch()
        self.insights_card.setMinimumWidth(260)
        self.panorama = ResponsivePair(self.evolution_card, self.insights_card)
        self.page_layout.addWidget(self.panorama)
        self.concentration_panel = ConcentrationPanel()
        self.page_layout.addWidget(self.concentration_panel)
        self.valuation_chart_card = SectionCard(
            "Contribuição de cada ativo para o resultado em aberto • BRL"
        )
        self.valuation_chart: QChartView | None = None
        self.chart_feedback = QLabel("Aguardando cotações.")
        self.chart_feedback.setWordWrap(True)
        self.valuation_chart_card.content.addWidget(self.chart_feedback)
        self.page_layout.addWidget(self.valuation_chart_card)
        detail_card = SectionCard("Conferência das posições")
        toggle = QPushButton("Mostrar / ocultar detalhes das posições")
        toggle.setObjectName("LinkButton")
        detail_card.content.addWidget(toggle)
        self.positions_table = DataTable(MARKET_HEADERS, [])
        self.positions_table.setVisible(False)
        toggle.clicked.connect(
            lambda: self.positions_table.setVisible(
                not self.positions_table.isVisible()
            )
        )
        detail_card.content.addWidget(self.positions_table)
        self.positions_empty = QLabel("Selecione uma carteira.")
        detail_card.content.addWidget(self.positions_empty)
        self.market_feedback = QLabel("Cotações indisponíveis.")
        self.market_feedback.setWordWrap(True)
        detail_card.content.addWidget(self.market_feedback)
        self.page_layout.addWidget(detail_card)
        quick = QHBoxLayout()
        for text, kind in (
            ("+ Registrar operação", "transaction"),
            ("+ Pesquisar ativo", "asset"),
            ("+ Criar meta", "goal"),
            ("+ Criar alerta", "alert"),
        ):
            button = QPushButton(text)
            button.setObjectName("QuickAction")
            button.setProperty("dialogKey", kind)
            button.clicked.connect(
                lambda _checked=False, action=kind: self.dialog_requested.emit(action)
            )
            quick.addWidget(button)
        self.page_layout.addLayout(quick)

    def set_history(self, history: list[Transaction]) -> None:
        if self.timeline_chart is not None:
            self.evolution_card.content.removeWidget(self.timeline_chart)
            self.timeline_chart.deleteLater()
            self.timeline_chart = None
        points = ledger_timeline(history)
        self.timeline_note.setText(
            "Custo aberto no fim dos meses com operações • não é patrimônio histórico de mercado. Passe o mouse nos pontos."
            if points
            else "Sem operações. Registre uma compra para começar."
        )
        if not points:
            return
        self.timeline_chart = capital_timeline_chart(
            [
                (
                    datetime.strptime(point.month, "%Y-%m").replace(
                        tzinfo=timezone.utc
                    ),
                    point.cost,
                )
                for point in points
            ]
        )
        self.evolution_card.content.addWidget(self.timeline_chart)

    def set_financial_data(
        self,
        portfolio_id: int | None,
        portfolios_count: int | None,
        result: ReconstructionResult,
        summary: FinancialSummary | None,
    ) -> None:
        self.context_label.setText(
            f"Carteira #{portfolio_id} • acompanhe risco, resultado e trajetória"
            if portfolio_id
            else "Selecione uma carteira para começar."
        )
        self.metrics["portfolios"].set_value(
            str(portfolios_count) if portfolios_count is not None else "—"
        )
        values = (
            {
                "positions": str(summary.positions_count),
                "cost": money_text(summary.cost_basis),
                "realized": money_text(summary.realized_profit_loss),
                "transactions": str(summary.transactions_count),
            }
            if summary
            else {}
        )
        for key in ("positions", "cost", "realized", "transactions"):
            self.metrics[key].set_value(values.get(key, "—"))
        replace_rows(
            self.positions_table, [row + ("—",) * 4 for row in position_rows(result)]
        )
        self.positions_empty.setText(
            "Nenhuma posição aberta." if portfolio_id else "Selecione uma carteira."
        )
        self.positions_empty.setVisible(not result.positions)

    def clear_market_data(self, message: str) -> None:
        self.concentration_panel.clear(message)
        self._clear_valuation_chart()
        self.chart_feedback.setText(message)
        self.insights_label.setText(message)
        for key in ("market", "unrealized", "total", "return"):
            self.metrics[key].set_value("—")
        self.market_feedback.setText(message)

    def set_market_data(self, valuation: PortfolioValuation) -> None:
        self.concentration_panel.display(valuation)
        for key, amount in (
            ("market", valuation.current_market_value),
            ("unrealized", valuation.unrealized_profit_loss),
            ("total", valuation.total_profit_loss),
        ):
            state = (
                "accent"
                if key == "market" and amount is not None
                else "positive"
                if amount is not None and amount > 0
                else "negative"
                if amount is not None and amount < 0
                else "neutral"
            )
            self.metrics[key].set_value(currency_text(amount), state)
        value = valuation.unrealized_return
        self.metrics["return"].set_value(
            percent_text(value),
            "positive"
            if value is not None and value > 0
            else "negative"
            if value is not None and value < 0
            else "neutral",
        )
        apply_valuation(self.positions_table, valuation)
        self.market_feedback.setText(market_status(valuation))
        self._clear_valuation_chart()
        available = [
            p for p in valuation.positions if p.unrealized_profit_loss is not None
        ]
        ranked = sorted(available, key=lambda p: p.unrealized_profit_loss or Decimal(0))
        concentration = valuation.concentration
        text = []
        if concentration.weights:
            top = concentration.weights[0]
            text.append(
                f"Maior exposição: {top.asset.symbol} • {percent_text(top.weight)} do valor aberto."
            )
        if ranked:
            best, worst = ranked[-1], ranked[0]
            text.append(
                f"Maior contribuição: {best.position.asset.symbol} • {currency_text(best.unrealized_profit_loss)}."
            )
            text.append(
                f"Menor contribuição: {worst.position.asset.symbol} • {currency_text(worst.unrealized_profit_loss)}."
            )
        if not valuation.complete:
            text.append(
                "Cobertura incompleta: totais e concentração indisponíveis. Confira as fontes nas posições."
            )
        self.insights_label.setText(
            "\n\n".join(text) or "Sem posições cotadas para analisar."
        )
        self.chart_feedback.setText(
            "Resultado monetário por posição = valor atual − custo aberto. Somente ativos com base BRL disponível; confira cobertura nos detalhes."
        )
        if ranked:
            self.valuation_chart = bar_chart(
                [p.position.asset.symbol for p in ranked],
                (
                    (
                        "Ganho em aberto",
                        [
                            float(
                                max(p.unrealized_profit_loss or Decimal(0), Decimal(0))
                            )
                            for p in ranked
                        ],
                        "#3DDC84",
                    ),
                    (
                        "Perda em aberto",
                        [
                            float(
                                min(p.unrealized_profit_loss or Decimal(0), Decimal(0))
                            )
                            for p in ranked
                        ],
                        "#FF5C6C",
                    ),
                ),
                260,
            )
            self.valuation_chart_card.content.addWidget(self.valuation_chart)

    def _clear_valuation_chart(self) -> None:
        if self.valuation_chart is not None:
            self.valuation_chart_card.content.removeWidget(self.valuation_chart)
            self.valuation_chart.deleteLater()
            self.valuation_chart = None

    def set_account(self, snapshot: AccountSnapshot | None) -> None:
        if not hasattr(self, "cash_card"):
            self.cash_card = MetricCard(
                "CAIXA DISPONÍVEL BRL",
                "—",
                tooltip="Saldo inicial + aportes − retiradas − compras + vendas + proventos líquidos − custos. Abertura explícita em Movimentações; o custo das posições não é caixa.",
            )
            self.equity_card = MetricCard(
                "PATRIMÔNIO COM CAIXA BRL",
                "—",
                tooltip="Caixa reconstruído + valor das posições com cotação BRL completa. Não inclui dívidas pessoais; não é o retorno temporal.",
            )
            row = QHBoxLayout()
            row.addWidget(self.cash_card)
            row.addWidget(self.equity_card)
            self.page_layout.insertLayout(1, row)
        self.cash_card.set_value(
            currency_text(snapshot.cash.balance if snapshot else None)
        )
        self.equity_card.set_value(currency_text(snapshot.equity if snapshot else None))
