from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
)

from nexo.ui.components.charts import line_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    filter_buttons,
)
from nexo.ui.demo.data import ALERTS, DEMO_NOTICE, GOALS


class GoalsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("goals")
        top = QHBoxLayout()
        top.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        top.addStretch()
        create = QPushButton("+  Nova meta")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(lambda: self.dialog_requested.emit("goal"))
        top.addWidget(create)
        self.page_layout.addLayout(top)
        self.page_layout.addLayout(filter_buttons(("Todas", "Curto prazo", "Médio prazo", "Longo prazo", "Concluídas")))

        cards = QGridLayout()
        cards.setSpacing(14)
        for index, goal in enumerate(GOALS):
            cards.addWidget(self._goal_card(*goal), 0, index)
        self.page_layout.addLayout(cards)

        evolution = SectionCard("Evolução das metas")
        evolution.content.addWidget(
            line_chart(
                (("Valor acumulado", [12, 16, 20, 25, 31, 38, 44, 52, 61, 69, 76, 84], "#10C7C7"),),
                250,
            )
        )
        self.page_layout.addWidget(evolution)

    @staticmethod
    def _goal_card(name: str, category: str, current: str, target: str, progress: int, deadline: str) -> SectionCard:
        card = SectionCard(name, "Editar")
        category_badge = Badge(category)
        current_label = QLabel(current)
        current_label.setObjectName("MetricValue")
        target_label = QLabel(f"de {target}  •  prazo {deadline}")
        target_label.setObjectName("SecondaryText")
        progress_bar = QProgressBar()
        progress_bar.setValue(progress)
        progress_bar.setTextVisible(False)
        percentage = QLabel(f"{progress}% concluído")
        percentage.setObjectName("AccentText")
        card.content.addWidget(category_badge)
        card.content.addWidget(current_label)
        card.content.addWidget(target_label)
        card.content.addWidget(progress_bar)
        card.content.addWidget(percentage)
        return card


class AlertsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("alerts")
        top = QHBoxLayout()
        top.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        top.addStretch()
        create = QPushButton("+  Criar alerta")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(lambda: self.dialog_requested.emit("alert"))
        top.addWidget(create)
        self.page_layout.addLayout(top)
        self.page_layout.addLayout(filter_buttons(("Ativos", "Carteira", "Metas", "Sistema")))

        active = SectionCard("Alertas configurados")
        rows = []
        for name, condition, state, checked in ALERTS:
            rows.append((name, condition, state, checked, "Ativo"))
        active.content.addWidget(
            DataTable(("NOME", "CONDIÇÃO", "ESTADO", "ÚLTIMA VERIFICAÇÃO", "STATUS"), rows)
        )
        toggles = QHBoxLayout()
        toggles.addWidget(QLabel("Controle rápido:"))
        for label in ("PETR4", "Reserva", "Alocação"):
            toggle = QCheckBox(label)
            toggle.setChecked(True)
            toggle.setToolTip("Alteração apenas visual nesta etapa.")
            toggles.addWidget(toggle)
        toggles.addStretch()
        active.content.addLayout(toggles)
        self.page_layout.addWidget(active)

        history = SectionCard("Histórico de alertas", "Ver histórico completo")
        history.content.addWidget(
            DataTable(
                ("DATA", "ALERTA", "EVENTO", "CANAL"),
                (
                    ("08/09/2026 14:32", "PETR4", "Preço atingiu R$ 31,45", "Aplicativo"),
                    ("02/09/2026 09:10", "Reserva", "Meta atingiu 90%", "Aplicativo"),
                    ("28/08/2026 18:04", "Alocação", "Desvio superior a 5%", "Aplicativo"),
                ),
            )
        )
        self.page_layout.addWidget(history)
        self.page_layout.addStretch()
