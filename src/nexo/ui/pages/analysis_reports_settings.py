from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
)

from nexo.ui.components.charts import bar_chart, donut_chart, line_chart
from nexo.ui.components.common import (
    Badge,
    PageContent,
    SectionCard,
    connect_planned_action,
)
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.demo.data import ALLOCATION, DEMO_NOTICE
from nexo.ui.icons import icon


class AnalysisPage(PageContent):
    def __init__(self) -> None:
        super().__init__("analysis")
        self.page_layout.addWidget(Badge(DEMO_NOTICE, "DemoBadge"), alignment=Qt.AlignmentFlag.AlignLeft)
        metrics = QGridLayout()
        metrics.setSpacing(12)
        values = (
            ("RENTABILIDADE", "+12,42%", "No período selecionado"),
            ("VOLATILIDADE", "14,8%", "Estimativa demonstrativa"),
            ("CONCENTRAÇÃO", "34%", "Maior classe"),
            ("DIVERSIFICAÇÃO", "Boa", "6 classes"),
            ("DRAWDOWN", "-8,4%", "Maior queda"),
            ("DIVIDENDOS", "R$ 3.240", "Últimos 12 meses"),
        )
        for index, (label, value, detail) in enumerate(values):
            metrics.addWidget(MetricCard(label, value, detail, icon("analytics", "#10C7C7")), index // 3, index % 3)
        self.page_layout.addLayout(metrics)

        first = QGridLayout()
        first.setSpacing(14)
        cumulative = SectionCard("Rentabilidade acumulada")
        cumulative.content.addWidget(
            line_chart(
                (
                    ("Carteira", [100, 102, 104, 103, 107, 109, 112, 115], "#10C7C7"),
                    ("CDI", [100, 101, 102, 103, 104, 105, 106, 107], "#4D7CFF"),
                    ("Ibovespa", [100, 98, 104, 101, 106, 105, 110, 108], "#FFB020"),
                )
            )
        )
        monthly = SectionCard("Rentabilidade mensal")
        monthly.content.addWidget(
            bar_chart(["Abr", "Mai", "Jun", "Jul", "Ago", "Set"], (("Rentabilidade", [1.2, 0.8, 1.9, -0.4, 2.1, 1.4], "#10C7C7"),))
        )
        first.addWidget(cumulative, 0, 0)
        first.addWidget(monthly, 0, 1)
        self.page_layout.addLayout(first)

        second = QGridLayout()
        by_class = SectionCard("Distribuição por classe")
        by_class.content.addWidget(donut_chart(ALLOCATION))
        by_sector = SectionCard("Distribuição por setor")
        sectors = [
            ("Financeiro", 29, "", "#10C7C7"),
            ("Commodities", 24, "", "#4D7CFF"),
            ("Energia", 18, "", "#8B6CFF"),
            ("Consumo", 16, "", "#3DDC84"),
            ("Outros", 13, "", "#6E7D91"),
        ]
        by_sector.content.addWidget(donut_chart(sectors))
        compare = SectionCard("Comparação")
        for label, value, kind in (("Carteira", "+12,42%", "Positive"), ("CDI", "+8,10%", "AccentText"), ("Ibovespa", "+6,72%", "Warning")):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addStretch()
            result = QLabel(value)
            result.setObjectName(kind)
            row.addWidget(result)
            compare.content.addLayout(row)
        second.addWidget(by_class, 0, 0)
        second.addWidget(by_sector, 0, 1)
        second.addWidget(compare, 0, 2)
        self.page_layout.addLayout(second)


class ReportsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("reports")
        self.page_layout.addWidget(Badge(DEMO_NOTICE, "DemoBadge"), alignment=Qt.AlignmentFlag.AlignLeft)
        options = QGridLayout()
        options.setSpacing(14)
        report_names = (
            ("Relatório da carteira", "Posições, alocação e resumo consolidado."),
            ("Relatório de movimentações", "Histórico filtrado de compras, vendas e aportes."),
            ("Relatório de rentabilidade", "Evolução e comparação por período."),
            ("Relatório de proventos", "Proventos recebidos e evolução mensal."),
            ("Planejamento financeiro", "Receitas, despesas e capacidade de aporte."),
        )
        for index, (title, description) in enumerate(report_names):
            card = SectionCard(title)
            text = QLabel(description)
            text.setObjectName("SecondaryText")
            text.setWordWrap(True)
            select = QPushButton("Selecionar")
            select.setObjectName("LinkButton")
            connect_planned_action(select)
            card.content.addWidget(text)
            card.content.addWidget(select, alignment=Qt.AlignmentFlag.AlignLeft)
            options.addWidget(card, index // 3, index % 3)
        self.page_layout.addLayout(options)

        generator = SectionCard("Gerar relatório")
        filters = QHBoxLayout()
        for items in (
            ["Longo Prazo", "Reserva", "Internacional"],
            ["Este mês", "3 meses", "6 meses", "1 ano", "Máximo"],
            ["PDF", "CSV"],
        ):
            combo = QComboBox()
            combo.addItems(items)
            filters.addWidget(combo)
        generate = QPushButton("Gerar relatório")
        generate.setObjectName("PrimaryButton")
        generate.clicked.connect(lambda: self.dialog_requested.emit("report"))
        filters.addStretch()
        filters.addWidget(generate)
        generator.content.addLayout(filters)
        self.page_layout.addWidget(generator)
        self.page_layout.addStretch()


class SettingsPage(PageContent):
    def __init__(self) -> None:
        super().__init__("settings")
        grid = QGridLayout()
        grid.setSpacing(14)
        grid.addWidget(self._appearance(), 0, 0)
        grid.addWidget(self._currency(), 0, 1)
        grid.addWidget(self._market(), 1, 0)
        grid.addWidget(self._notifications(), 1, 1)
        grid.addWidget(self._privacy(), 2, 0)
        grid.addWidget(self._local_data(), 2, 1)
        grid.addWidget(self._about(), 3, 0, 1, 2)
        self.page_layout.addLayout(grid)

    @staticmethod
    def _appearance() -> SectionCard:
        card = SectionCard("Aparência")
        for label, enabled, checked in (("Dark", True, True), ("Light  ·  Em breve", False, False), ("Sistema  ·  Em breve", False, False)):
            option = QRadioButton(label)
            option.setEnabled(enabled)
            option.setChecked(checked)
            card.content.addWidget(option)
        return card

    @staticmethod
    def _currency() -> SectionCard:
        card = SectionCard("Moeda")
        text = QLabel("Moeda principal")
        text.setObjectName("SecondaryText")
        combo = QComboBox()
        combo.addItem("BRL — Real brasileiro")
        card.content.addWidget(text)
        card.content.addWidget(combo)
        return card

    @staticmethod
    def _market() -> SectionCard:
        card = SectionCard("Dados de mercado")
        card.content.addWidget(QLabel("Provider: ainda não configurado"))
        card.content.addWidget(Badge("Desconectado", "WarningBadge"), alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    @staticmethod
    def _notifications() -> SectionCard:
        card = SectionCard("Notificações")
        card.content.addWidget(QLabel("Alertas no aplicativo serão conectados futuramente."))
        card.content.addWidget(Badge("Em breve", "MutedBadge"), alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    @staticmethod
    def _privacy() -> SectionCard:
        card = SectionCard("Privacidade")
        text = QLabel("Os dados financeiros serão armazenados localmente quando a persistência for implementada.")
        text.setObjectName("SecondaryText")
        text.setWordWrap(True)
        card.content.addWidget(text)
        return card

    @staticmethod
    def _local_data() -> SectionCard:
        card = SectionCard("Dados locais")
        card.content.addWidget(QLabel("Banco local: ainda não criado"))
        for label in ("Exportar dados", "Limpar dados"):
            button = QPushButton(label)
            button.setObjectName("SecondaryButton")
            button.setEnabled(False)
            button.setToolTip("Disponível após a implementação da persistência.")
            card.content.addWidget(button)
        return card

    @staticmethod
    def _about() -> SectionCard:
        card = SectionCard("Sobre")
        card.content.addWidget(QLabel("NEXO  •  versão 0.1.0  •  Projeto acadêmico de Programação Orientada a Objetos"))
        return card


from PySide6.QtCore import Qt
