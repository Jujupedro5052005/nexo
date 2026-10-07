from PySide6.QtCharts import QChartView
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from nexo.application.portfolio.financial_summary import FinancialSummary
from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.reconstruction import ReconstructionResult
from nexo.ui.components.charts import bar_chart, line_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    connect_planned_action,
)
from nexo.ui.components.concentration_panel import ConcentrationPanel
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.components.responsive_pair import ResponsivePair
from nexo.ui.demo.data import (
    ALERTS,
    DEMO_NOTICE,
    GOALS,
    INVESTED_SERIES,
    PORTFOLIO_SERIES,
    REFERENCE_SERIES,
)
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
from nexo.ui.icons import icon


class OverviewPage(PageContent):
    """Real ledger metrics above explicitly separated presentation demos."""

    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("overview")
        self.page_layout.addWidget(Badge("Dados locais do ledger"))
        self.context_label = QLabel(
            "Selecione uma carteira para consultar suas posições."
        )
        self.page_layout.addWidget(self.context_label)
        local_metrics = self._metrics()
        market_metrics = QHBoxLayout()
        for key, title in (
            ("market", "VALOR DAS POSIÇÕES"),
            ("unrealized", "NÃO REALIZADO"),
            ("total", "RESULTADO TOTAL"),
            ("return", "RETORNO DAS POSIÇÕES ABERTAS"),
        ):
            detail = {
                "market": "Posições abertas em BRL • sem caixa",
                "unrealized": "Valor atual menos custo aberto",
                "total": "Realizado + não realizado",
                "return": "Não realizado / custo aberto",
            }[key]
            metric = MetricCard(title, "—", detail)
            if key == "market":
                metric.setProperty("highlight", True)
            self.metrics[key] = metric
            market_metrics.addWidget(metric, 1)
        self.page_layout.addLayout(market_metrics)
        self.page_layout.addLayout(local_metrics)
        positions = SectionCard("Posições abertas — carteira selecionada")
        self.positions_table = DataTable(MARKET_HEADERS, [])
        self.positions_table.setObjectName("overview_positions_table")
        positions.content.addWidget(self.positions_table)
        self.positions_empty = QLabel("Selecione uma carteira.")
        positions.content.addWidget(self.positions_empty)
        self.market_feedback = QLabel("Cotações e valor de mercado indisponíveis.")
        self.market_feedback.setWordWrap(True)
        positions.content.addWidget(self.market_feedback)
        self.page_layout.addWidget(positions)
        self.concentration_panel = ConcentrationPanel()
        self.page_layout.addWidget(self.concentration_panel)
        self.valuation_chart_card = SectionCard(
            "Custo e valor das posições cotadas — BRL"
        )
        self.valuation_chart: QChartView | None = None
        self.chart_feedback = QLabel(
            "Aguardando cotações. Sem série demonstrativa nesta seção."
        )
        self.valuation_chart_card.content.addWidget(self.chart_feedback)
        self.page_layout.addWidget(self.valuation_chart_card)
        demo_row = QHBoxLayout()
        demo_row.addWidget(Badge("Seções abaixo: dados demonstrativos", "DemoBadge"))
        demo_row.addStretch()
        self.page_layout.addLayout(demo_row)

        self.evolution_card = self._evolution()
        self.insights_card = self._insights()
        self.demo_charts = ResponsivePair(self.evolution_card, self.insights_card)
        self.page_layout.addWidget(self.demo_charts)

        lower = QGridLayout()
        lower.setSpacing(14)
        lower.addWidget(self._cashflow(), 0, 0)
        lower.addWidget(self._goals(), 0, 1)
        lower.setColumnStretch(0, 1)
        lower.setColumnStretch(1, 1)
        self.page_layout.addLayout(lower)

        bottom = QGridLayout()
        bottom.setSpacing(14)
        bottom.addWidget(self._alerts(), 0, 0, 1, 2)
        bottom.addWidget(self._quick_actions(), 0, 2)
        bottom.setColumnStretch(0, 2)
        bottom.setColumnStretch(1, 2)
        bottom.setColumnStretch(2, 2)
        self.page_layout.addLayout(bottom)

    def _metrics(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        self.metrics: dict[str, MetricCard] = {}
        for key, label in (
            ("portfolios", "CARTEIRAS"),
            ("positions", "POSIÇÕES ABERTAS"),
            ("cost", "CUSTO DAS POSIÇÕES"),
            ("realized", "RESULTADO REALIZADO"),
            ("transactions", "MOVIMENTAÇÕES"),
        ):
            card = MetricCard(label, "—", "Ledger local")
            self.metrics[key] = card
            row.addWidget(card, 1)
        return row

    def set_financial_data(
        self,
        portfolio_id: int | None,
        portfolios_count: int | None,
        result: ReconstructionResult,
        summary: FinancialSummary | None,
    ) -> None:
        self.metrics["portfolios"].value_label.setText(
            str(portfolios_count) if portfolios_count is not None else "—"
        )
        self.context_label.setText(
            f"Carteira #{portfolio_id} • valores a custo e resultado realizado"
            if portfolio_id
            else "Selecione uma carteira para consultar suas posições."
        )
        values = (
            {
                "positions": str(summary.positions_count),
                "cost": money_text(summary.cost_basis),
                "realized": money_text(summary.realized_profit_loss),
                "transactions": str(summary.transactions_count),
            }
            if summary is not None
            else {}
        )
        for key in ("positions", "cost", "realized", "transactions"):
            amount = summary.realized_profit_loss if summary is not None and key == "realized" else None
            state = "positive" if amount is not None and amount > 0 else "negative" if amount is not None and amount < 0 else "neutral"
            self.metrics[key].set_value(values.get(key, "—"), state)
        replace_rows(
            self.positions_table, [row + ("—",) * 4 for row in position_rows(result)]
        )
        self.positions_empty.setVisible(not result.positions)
        self.positions_empty.setText(
            "Nenhuma posição aberta nesta carteira."
            if portfolio_id
            else "Selecione uma carteira."
        )

    def clear_market_data(self, message: str) -> None:
        self.concentration_panel.clear(message)
        self._clear_valuation_chart()
        self.chart_feedback.setText(message)
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
            state = "accent" if key == "market" and amount is not None else "positive" if amount is not None and amount > 0 else "negative" if amount is not None and amount < 0 else "neutral"
            self.metrics[key].set_value(currency_text(amount), state)
        return_value = valuation.unrealized_return
        self.metrics["return"].set_value(percent_text(return_value),
            "positive" if return_value is not None and return_value > 0 else "negative" if return_value is not None and return_value < 0 else "neutral")
        apply_valuation(self.positions_table, valuation)
        self.market_feedback.setText(market_status(valuation))
        self._clear_valuation_chart()
        available = [
            item
            for item in valuation.positions
            if item.quote is not None
            and item.quote.currency == "BRL"
            and item.market_value is not None
        ]
        self.chart_feedback.setText(
            "Somente posições BRL com cotação disponível; valores de mercado das posições abertas, sem caixa."
            if available
            else "Nenhuma posição BRL com cotação para exibir."
        )
        if available:
            # Qt chart coordinates are floats; all financial calculations stay Decimal.
            self.valuation_chart = bar_chart(
                [item.position.asset.symbol for item in available],
                (
                    (
                        "Custo do ledger",
                        [float(item.position.cost_basis) for item in available],
                        "#4D7CFF",
                    ),
                    (
                        "Valor atual",
                        [
                            float(item.market_value)
                            for item in available
                            if item.market_value is not None
                        ],
                        "#10C7C7",
                    ),
                ),
            )
            self.valuation_chart_card.content.addWidget(self.valuation_chart)

    def _clear_valuation_chart(self) -> None:
        if self.valuation_chart is not None:
            self.valuation_chart_card.content.removeWidget(self.valuation_chart)
            self.valuation_chart.deleteLater()
            self.valuation_chart = None

    @staticmethod
    def _evolution() -> SectionCard:
        card = SectionCard("Evolução Patrimonial")
        card.content.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        filters = QHBoxLayout()
        filters.addStretch()
        for label in ("1M", "3M", "6M", "1A", "Máx"):
            button = QPushButton(label)
            button.setObjectName("FilterButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setChecked(label == "1A")
            filters.addWidget(button)
        card.content.addLayout(filters)
        card.content.addWidget(
            line_chart(
                (
                    ("Patrimônio", PORTFOLIO_SERIES, "#10C7C7"),
                    ("Valor investido", INVESTED_SERIES, "#4D7CFF"),
                    ("Referência", REFERENCE_SERIES, "#6E7D91"),
                ),
                250,
            )
        )
        return card

    @staticmethod
    def _insights() -> SectionCard:
        card = SectionCard("NEXO Insights")
        card.content.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        card.setMinimumWidth(260)
        badge = Badge("ATENÇÃO", "WarningBadge")
        title = QLabel("Concentração da carteira")
        title.setObjectName("SectionTitle")
        text = QLabel(
            "A parcela demonstrativa em renda variável está acima da alocação alvo configurada para esta estratégia."
        )
        text.setObjectName("SecondaryText")
        text.setWordWrap(True)
        action = QPushButton("Ver análise completa  →")
        action.setObjectName("LinkButton")
        connect_planned_action(action)
        dots = QLabel("●  ○  ○")
        dots.setObjectName("AccentText")
        card.content.addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft)
        card.content.addWidget(title)
        card.content.addWidget(text)
        card.content.addStretch()
        card.content.addWidget(action, alignment=Qt.AlignmentFlag.AlignLeft)
        card.content.addWidget(dots, alignment=Qt.AlignmentFlag.AlignCenter)
        return card

    @staticmethod
    def _cashflow() -> SectionCard:
        card = SectionCard("Fluxo Financeiro")
        card.content.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        stats = QHBoxLayout()
        for label, value, kind in (
            ("Entradas", "R$ 9.800", "Positive"),
            ("Saídas", "R$ 6.420", "Negative"),
            ("Disponível", "R$ 3.380", "AccentText"),
        ):
            column = QVBoxLayout()
            caption = QLabel(label)
            caption.setObjectName("SecondaryText")
            amount = QLabel(value)
            amount.setObjectName(kind)
            column.addWidget(caption)
            column.addWidget(amount)
            stats.addLayout(column)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(65)
        bar.setTextVisible(False)
        capacity = QLabel("Capacidade de aporte   R$ 3.380 / mês")
        capacity.setObjectName("MetricDetail")
        card.content.addLayout(stats)
        card.content.addWidget(bar)
        card.content.addWidget(capacity)
        return card

    @staticmethod
    def _goals() -> SectionCard:
        card = SectionCard("Metas", "Ver todas")
        card.content.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        for name, _category, current, target, progress, _deadline in GOALS[:2]:
            title = QLabel(f"{name}    {progress}%")
            title.setObjectName("SectionTitle")
            value = QLabel(f"{current} de {target}")
            value.setObjectName("SecondaryText")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(progress)
            bar.setTextVisible(False)
            card.content.addWidget(title)
            card.content.addWidget(value)
            card.content.addWidget(bar)
        return card

    @staticmethod
    def _alerts() -> SectionCard:
        card = SectionCard("Alertas Recentes", "Ver todos  →")
        card.content.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        for name, _condition, _state, checked in ALERTS:
            row = QHBoxLayout()
            marker = QLabel("●")
            marker.setObjectName("Warning")
            label = QLabel(name)
            when = QLabel(checked)
            when.setObjectName("SecondaryText")
            row.addWidget(marker)
            row.addWidget(label)
            row.addStretch()
            row.addWidget(when)
            card.content.addLayout(row)
        return card

    def _quick_actions(self) -> SectionCard:
        card = SectionCard("Ações rápidas")
        actions = (
            ("Registrar movimentação", "transaction"),
            ("Adicionar ativo", "asset"),
            ("Criar alerta", "alert"),
            ("Criar meta", "goal"),
        )
        grid = QGridLayout()
        for index, (label, key) in enumerate(actions):
            button = QPushButton(label)
            button.setObjectName("QuickAction")
            button.setProperty("dialogKey", key)
            button.setIcon(icon("plus", "#10C7C7"))
            button.clicked.connect(
                lambda _checked=False, value=key: self.dialog_requested.emit(value)
            )
            grid.addWidget(button, index // 2, index % 2)
        card.content.addLayout(grid)
        return card
