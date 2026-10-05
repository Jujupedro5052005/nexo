from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.ui.components.charts import line_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    connect_planned_action,
    filter_buttons,
)
from nexo.ui.components.empty_state import EmptyState
from nexo.ui.demo.data import ASSETS, DEMO_NOTICE


class PortfoliosPage(PageContent):
    dialog_requested = Signal(str)
    portfolio_selected = Signal(int)

    def __init__(self, list_portfolios: ListPortfolios) -> None:
        super().__init__("portfolios")
        self._list_portfolios = list_portfolios
        self._portfolios: list[Portfolio] = []
        self.selected_portfolio_id: int | None = None
        self.selection_buttons: dict[int, QPushButton] = {}
        actions = QHBoxLayout()
        actions.addWidget(Badge("Carteiras locais"))
        actions.addStretch()
        refresh = QPushButton("Atualizar")
        refresh.setObjectName("SecondaryButton")
        refresh.clicked.connect(self.reload)
        actions.addWidget(refresh)
        create = QPushButton("+  Nova carteira")
        create.setObjectName("PrimaryButton")
        create.setProperty("action", "create_portfolio")
        create.clicked.connect(lambda: self.dialog_requested.emit("portfolio"))
        actions.addWidget(create)
        self.page_layout.addLayout(actions)

        self.selection_label = QLabel("Nenhuma carteira selecionada")
        self.selection_label.setObjectName("SecondaryText")
        self.page_layout.addWidget(self.selection_label)
        self.feedback = QLabel()
        self.feedback.setObjectName("WarningBadge")
        self.feedback.setWordWrap(True)
        self.feedback.hide()
        self.page_layout.addWidget(self.feedback)
        self.empty_state = EmptyState(
            "Nenhuma carteira cadastrada",
            "Crie sua primeira carteira para organizar seus investimentos.",
            "Nova carteira",
        )
        self.empty_state.setObjectName("portfolios_empty_state")
        self.empty_state.action_requested.connect(
            lambda: self.dialog_requested.emit("portfolio")
        )
        self.empty_state.hide()
        self.page_layout.addWidget(self.empty_state)
        self.cards = QGridLayout()
        self.cards.setSpacing(14)
        self.page_layout.addLayout(self.cards)
        self.page_layout.addStretch()
        self.reload()

    def reload(self) -> bool:
        """Replace displayed data only after a successful repository read."""
        try:
            portfolios = self._list_portfolios.execute()
        except PortfolioRepositoryError:
            self.feedback.setText("Não foi possível carregar as carteiras. Tente atualizar.")
            self.feedback.show()
            return False
        self.feedback.hide()
        self._portfolios = portfolios
        self.selection_buttons.clear()
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item is not None and (widget := item.widget()) is not None:
                widget.setParent(None)
                widget.deleteLater()
        for index, portfolio in enumerate(portfolios):
            self.cards.addWidget(self._portfolio_card(portfolio), index // 2, index % 2)
        self.empty_state.setVisible(not portfolios)
        self.set_selected_portfolio(self.selected_portfolio_id)
        return True

    def _portfolio_card(self, portfolio: Portfolio) -> SectionCard:
        card = SectionCard(portfolio.name)
        card.setProperty("portfolioId", portfolio.id)
        card.content.addWidget(Badge(f"Carteira #{portfolio.id}"))
        card.content.addWidget(QLabel("Carteira vazia"))
        metadata = QLabel("0 ativos  •  Sem movimentações")
        metadata.setObjectName("SecondaryText")
        card.content.addWidget(metadata)
        if portfolio.id is not None:
            button = QPushButton("Selecionar")
            button.setObjectName("FilterButton")
            button.setCheckable(True)
            button.setProperty("portfolioId", portfolio.id)
            button.setAccessibleName(f"Selecionar {portfolio.name}, carteira {portfolio.id}")
            button.clicked.connect(
                lambda _checked=False, portfolio_id=portfolio.id: self._select(portfolio_id)
            )
            self.selection_buttons[portfolio.id] = button
            card.content.addWidget(button)
        return card

    def set_selected_portfolio(self, portfolio_id: int | None) -> None:
        selected = next((p for p in self._portfolios if p.id == portfolio_id), None)
        self.selected_portfolio_id = selected.id if selected is not None else None
        self.selection_label.setText(
            f"Selecionada: {selected.name}  •  Carteira #{selected.id}"
            if selected is not None else "Nenhuma carteira selecionada"
        )
        for identity, button in self.selection_buttons.items():
            checked = identity == self.selected_portfolio_id
            button.setChecked(checked)
            button.setText("Selecionada" if checked else "Selecionar")

    def _select(self, portfolio_id: int) -> None:
        self.set_selected_portfolio(portfolio_id)
        if self.selected_portfolio_id is not None:
            self.portfolio_selected.emit(self.selected_portfolio_id)


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
