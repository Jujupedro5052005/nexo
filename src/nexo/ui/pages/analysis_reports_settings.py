from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
)

from nexo.application.assets.market_integration import (
    GetMarketIntegrationStatus,
    TestMarketConnection,
)
from nexo.application.assets.provider_status import GetProviderHealth
from nexo.ui.components.common import (
    Badge,
    PageContent,
    SectionCard,
    connect_planned_action,
)
from nexo.ui.components.market_integration_panel import MarketIntegrationPanel
from nexo.ui.components.provider_health_panel import ProviderHealthPanel
from nexo.ui.demo.data import DEMO_NOTICE
from nexo.ui.pages.analysis_page import AnalysisPage as AnalysisPage  # noqa: PLC0414


class ReportsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("reports")
        self.page_layout.addWidget(
            Badge(DEMO_NOTICE, "DemoBadge"), alignment=Qt.AlignmentFlag.AlignLeft
        )
        options = QGridLayout()
        options.setSpacing(14)
        report_names = (
            ("Relatório da carteira", "Posições, alocação e resumo consolidado."),
            (
                "Relatório de movimentações",
                "Histórico filtrado de compras, vendas e aportes.",
            ),
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
    def __init__(
        self,
        integration_status: GetMarketIntegrationStatus | None = None,
        test_connection: TestMarketConnection | None = None,
        provider_health: GetProviderHealth | None = None,
    ) -> None:
        super().__init__("settings")
        grid = QGridLayout()
        grid.setSpacing(14)
        grid.addWidget(self._appearance(), 0, 0)
        grid.addWidget(self._currency(), 0, 1)
        self.market_panel = MarketIntegrationPanel(integration_status, test_connection)
        grid.addWidget(self.market_panel, 1, 0)
        grid.addWidget(self._notifications(), 1, 1)
        grid.addWidget(self._privacy(), 2, 0)
        grid.addWidget(self._local_data(), 2, 1)
        grid.addWidget(self._about(), 3, 0, 1, 2)
        self.page_layout.addLayout(grid)
        self.provider_panel = ProviderHealthPanel(provider_health)
        self.page_layout.addWidget(self.provider_panel)

    @staticmethod
    def _appearance() -> SectionCard:
        card = SectionCard("Aparência")
        for label, enabled, checked in (
            ("Dark", True, True),
            ("Light  ·  Em breve", False, False),
            ("Sistema  ·  Em breve", False, False),
        ):
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
    def _notifications() -> SectionCard:
        card = SectionCard("Notificações")
        card.content.addWidget(
            QLabel("Alertas no aplicativo serão conectados futuramente.")
        )
        card.content.addWidget(
            Badge("Em breve", "MutedBadge"), alignment=Qt.AlignmentFlag.AlignLeft
        )
        return card

    @staticmethod
    def _privacy() -> SectionCard:
        card = SectionCard("Privacidade")
        text = QLabel(
            "Os dados financeiros serão armazenados localmente quando a persistência for implementada."
        )
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
        card.content.addWidget(
            QLabel(
                "NEXO  •  versão 0.1.0  •  Projeto acadêmico de Programação Orientada a Objetos"
            )
        )
        return card
