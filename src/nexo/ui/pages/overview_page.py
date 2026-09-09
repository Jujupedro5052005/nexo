from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from nexo.ui.components.charts import donut_chart, line_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    connect_planned_action,
)
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.demo.data import (
    ALERTS,
    ALLOCATION,
    DEMO_NOTICE,
    GOALS,
    INVESTED_SERIES,
    PORTFOLIO_SERIES,
    POSITIONS,
    REFERENCE_SERIES,
)
from nexo.ui.icons import icon


class OverviewPage(PageContent):
    """Full presentation prototype for the dashboard."""

    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("overview")
        demo_row = QHBoxLayout()
        demo_row.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        demo_row.addStretch()
        self.page_layout.addLayout(demo_row)
        self.page_layout.addLayout(self._metrics())

        charts = QGridLayout()
        charts.setSpacing(14)
        charts.addWidget(self._evolution(), 0, 0, 1, 2)
        charts.addWidget(self._allocation(), 0, 2)
        charts.setColumnStretch(0, 2)
        charts.setColumnStretch(1, 2)
        charts.setColumnStretch(2, 3)
        self.page_layout.addLayout(charts)

        middle = QGridLayout()
        middle.setSpacing(14)
        middle.addWidget(self._positions(), 0, 0, 1, 2)
        middle.addWidget(self._insights(), 0, 2)
        middle.setColumnStretch(0, 2)
        middle.setColumnStretch(1, 2)
        middle.setColumnStretch(2, 2)
        self.page_layout.addLayout(middle)

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

    @staticmethod
    def _metrics() -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        items = (
            ("PATRIMÔNIO TOTAL", "R$ 125.430,28", "+ R$ 4.820 este mês", "wallet", "positive", "Soma demonstrativa dos ativos da carteira."),
            ("RENTABILIDADE", "+12,42%", "+1,84% no período", "analytics", "positive", "Variação percentual acumulada da carteira no período selecionado."),
            ("RESULTADO", "+R$ 13.870,42", "Ganho não realizado", "overview", "positive", "Diferença demonstrativa entre valor atual e valor investido."),
            ("APORTE MÉDIO", "R$ 2.500,00", "Média dos últimos 6 meses", "cashflow", "neutral", "Média demonstrativa dos aportes mensais."),
        )
        for label, value, detail, icon_name, trend, tooltip in items:
            row.addWidget(
                MetricCard(label, value, detail, icon(icon_name, "#10C7C7"), trend, tooltip),
                1,
            )
        return row

    @staticmethod
    def _evolution() -> SectionCard:
        card = SectionCard("Evolução Patrimonial")
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
    def _allocation() -> SectionCard:
        card = SectionCard("Alocação da Carteira", "Ver carteira completa  →")
        row = QHBoxLayout()
        chart = donut_chart(ALLOCATION)
        chart.setMaximumWidth(255)
        row.addWidget(chart, 1)
        legend = QVBoxLayout()
        for category, percent, value, color in ALLOCATION:
            line = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color};")
            name = QLabel(category)
            name.setObjectName("SecondaryText")
            numbers = QLabel(f"{percent}%  ·  {value}")
            numbers.setObjectName("SecondaryText")
            line.addWidget(dot)
            line.addWidget(name)
            line.addStretch()
            line.addWidget(numbers)
            legend.addLayout(line)
        row.addLayout(legend, 2)
        card.content.addLayout(row)
        return card

    @staticmethod
    def _positions() -> SectionCard:
        card = SectionCard("Principais Posições", "Ver todas")
        table = DataTable(("ATIVO", "VALOR ATUAL", "PARTICIPAÇÃO", "RESULTADO"), POSITIONS)
        table.setMaximumHeight(255)
        for row in range(table.rowCount()):
            result = table.item(row, 3)
            result.setForeground(QColor("#3DDC84" if not result.text().startswith("-") else "#FF5C6C"))
        card.content.addWidget(table)
        return card

    @staticmethod
    def _insights() -> SectionCard:
        card = SectionCard("NEXO Insights")
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
            button.clicked.connect(lambda _checked=False, value=key: self.dialog_requested.emit(value))
            grid.addWidget(button, index // 2, index % 2)
        card.content.addLayout(grid)
        return card
