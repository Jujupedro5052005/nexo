from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QRadioButton,
)

from nexo.application.assets.market_integration import (
    GetMarketIntegrationStatus,
    TestMarketConnection,
)
from nexo.application.assets.provider_status import GetProviderHealth
from nexo.application.local_data import ManageLocalData
from nexo.ui.components.common import (
    Badge,
    PageContent,
    SectionCard,
)
from nexo.ui.components.local_data_panel import LocalDataPanel
from nexo.ui.components.market_integration_panel import MarketIntegrationPanel
from nexo.ui.components.provider_health_panel import ProviderHealthPanel
from nexo.ui.pages.analysis_page import AnalysisPage as AnalysisPage  # noqa: PLC0414
from nexo.ui.pages.reports_page import ReportsPage as ReportsPage  # noqa: PLC0414
from nexo.ui.preferences import select_theme, theme_choice


class SettingsPage(PageContent):
    def __init__(
        self,
        integration_status: GetMarketIntegrationStatus | None = None,
        test_connection: TestMarketConnection | None = None,
        provider_health: GetProviderHealth | None = None,
        local_data: ManageLocalData | None = None,
    ) -> None:
        super().__init__("settings")
        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.addWidget(self._appearance(), 0, 0)
        grid.addWidget(self._currency(), 0, 1)
        self.market_panel = MarketIntegrationPanel(integration_status, test_connection)
        grid.addWidget(self.market_panel, 1, 0)
        grid.addWidget(self._notifications(), 1, 1)
        grid.addWidget(self._privacy(), 2, 0)
        self.local_data_panel = LocalDataPanel(local_data)
        grid.addWidget(self.local_data_panel, 2, 1)
        grid.addWidget(self._about(), 3, 0, 1, 2)
        self.page_layout.addLayout(grid)
        self.provider_panel = ProviderHealthPanel(provider_health)
        self.page_layout.addWidget(self.provider_panel)

    @staticmethod
    def _appearance() -> SectionCard:
        card = SectionCard("Aparência")
        for label, value in (
            ("Escuro", "dark"),
            ("Claro", "light"),
            ("Sistema", "system"),
        ):
            option = QRadioButton(label)
            option.setObjectName(f"theme_{value}")
            option.setChecked(theme_choice() == value)
            option.toggled.connect(
                lambda checked, mode=value: select_theme(mode) if checked else None
            )
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
        text = QLabel(
            "Alertas de preço são persistidos e verificados manualmente na página Alertas. Sem envio externo."
        )
        text.setWordWrap(True)
        card.content.addWidget(text)
        card.content.addWidget(
            Badge("Verificação manual local", "Badge"),
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        return card

    @staticmethod
    def _privacy() -> SectionCard:
        card = SectionCard("Privacidade")
        text = QLabel(
            "Carteiras, movimentações, planejamento, metas e alertas são armazenados localmente em SQLite. Dados de mercado são consultados pelas fontes configuradas."
        )
        text.setObjectName("SecondaryText")
        text.setWordWrap(True)
        card.content.addWidget(text)
        return card

    @staticmethod
    def _about() -> SectionCard:
        card = SectionCard("Sobre")
        text = QLabel(
            "NEXO  •  versão 0.1.0  •  Projeto acadêmico de Programação Orientada a Objetos"
        )
        text.setWordWrap(True)
        card.content.addWidget(text)
        return card
