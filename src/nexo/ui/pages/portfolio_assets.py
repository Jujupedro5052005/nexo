from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from nexo.ui.components.charts import line_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    connect_planned_action,
    filter_buttons,
)
from nexo.ui.demo.data import ASSETS, DEMO_NOTICE, PORTFOLIOS


class PortfoliosPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("portfolios")
        actions = QHBoxLayout()
        actions.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        actions.addStretch()
        create = QPushButton("+  Nova carteira")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(lambda: self.dialog_requested.emit("portfolio"))
        actions.addWidget(create)
        self.page_layout.addLayout(actions)

        cards = QGridLayout()
        cards.setSpacing(14)
        for index, data in enumerate(PORTFOLIOS):
            cards.addWidget(self._portfolio_card(*data), 0, index)
        self.page_layout.addLayout(cards)

        compare = SectionCard("Comparar carteiras")
        description = QLabel("Selecione duas estratégias para visualizar uma comparação demonstrativa.")
        description.setObjectName("SecondaryText")
        fields = QHBoxLayout()
        first = QComboBox()
        second = QComboBox()
        names = [item[0] for item in PORTFOLIOS]
        first.addItems(names)
        second.addItems(names)
        second.setCurrentIndex(1)
        compare_button = QPushButton("Comparar")
        compare_button.setObjectName("SecondaryButton")
        connect_planned_action(
            compare_button,
            "A comparação real será conectada ao domínio em uma próxima etapa.",
        )
        fields.addWidget(first)
        fields.addWidget(QLabel("versus"))
        fields.addWidget(second)
        fields.addStretch()
        fields.addWidget(compare_button)
        compare.content.addWidget(description)
        compare.content.addLayout(fields)
        self.page_layout.addWidget(compare)
        self.page_layout.addStretch()

    def _portfolio_card(self, name: str, value: str, result: str, assets: str, updated: str) -> SectionCard:
        card = SectionCard(name)
        amount = QLabel(value)
        amount.setObjectName("MetricValue")
        gain = QLabel(result)
        gain.setObjectName("Positive")
        metadata = QLabel(f"{assets}  •  Atualizada {updated.lower()}")
        metadata.setObjectName("SecondaryText")
        buttons = QHBoxLayout()
        for label in ("Abrir", "Editar", "⋯"):
            button = QPushButton(label)
            button.setObjectName("LinkButton" if label != "⋯" else "IconButton")
            connect_planned_action(
                button, "Ação demonstrativa; será conectada ao domínio."
            )
            buttons.addWidget(button)
        buttons.addStretch()
        card.content.addWidget(amount)
        card.content.addWidget(gain)
        card.content.addWidget(metadata)
        card.content.addLayout(buttons)
        return card


class AssetsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("assets")
        top = QHBoxLayout()
        top.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        top.addStretch()
        self.page_layout.addLayout(top)
        search_row = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("asset_search")
        search.setPlaceholderText("Buscar ativo por código ou nome")
        search.setMinimumHeight(42)
        search_button = QPushButton("Buscar")
        search_button.setObjectName("PrimaryButton")
        connect_planned_action(
            search_button,
            "A consulta externa será conectada em uma próxima etapa.",
        )
        search_row.addWidget(search, 1)
        search_row.addWidget(search_button)
        self.page_layout.addLayout(search_row)
        self.page_layout.addLayout(filter_buttons(("Todos", "Ações", "FIIs", "ETFs", "Renda fixa", "Cripto", "Internacional")))

        body = QGridLayout()
        body.setSpacing(14)
        list_card = SectionCard("Ativos encontrados")
        table = DataTable(("CÓDIGO", "NOME", "TIPO", "PREÇO", "VARIAÇÃO", "NA CARTEIRA?"), ASSETS)
        table.setObjectName("assets_table")
        table.selectRow(0)
        list_card.content.addWidget(table)
        body.addWidget(list_card, 0, 0, 1, 2)
        body.addWidget(self._details(), 0, 2)
        body.setColumnStretch(0, 2)
        body.setColumnStretch(1, 2)
        body.setColumnStretch(2, 2)
        self.page_layout.addLayout(body)
        self.page_layout.addStretch()

    def _details(self) -> SectionCard:
        card = SectionCard("PETR4  ·  Petrobras PN")
        value = QLabel("R$ 36,82")
        value.setObjectName("MetricValue")
        change = QLabel("+1,24% hoje")
        change.setObjectName("Positive")
        stats = QGridLayout()
        for index, (label, amount) in enumerate((
            ("Máxima", "R$ 37,10"), ("Mínima", "R$ 35,92"),
            ("Volume", "R$ 1,2 bi"), ("P/L", "4,82"), ("Dividend Yield", "12,1%"),
        )):
            caption = QLabel(label)
            caption.setObjectName("SecondaryText")
            number = QLabel(amount)
            stats.addWidget(caption, (index // 2) * 2, index % 2)
            stats.addWidget(number, (index // 2) * 2 + 1, index % 2)
        card.content.addWidget(value)
        card.content.addWidget(change)
        card.content.addLayout(stats)
        card.content.addWidget(line_chart((("Preço", [34, 35, 34.6, 36, 35.8, 36.82], "#10C7C7"),), 170))
        actions = QVBoxLayout()
        for label, key in (("Adicionar à carteira", "asset"), ("Criar alerta", "alert"), ("Analisar ativo", "notice")):
            button = QPushButton(label)
            button.setObjectName("PrimaryButton" if key == "asset" else "SecondaryButton")
            button.clicked.connect(lambda _checked=False, value=key: self.dialog_requested.emit(value))
            actions.addWidget(button)
        card.content.addLayout(actions)
        return card
