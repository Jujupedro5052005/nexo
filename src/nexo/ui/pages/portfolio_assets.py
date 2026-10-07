from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from nexo.application.portfolio.financial_summary import FinancialSummary
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.reconstruction import ReconstructionResult
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
)
from nexo.ui.components.concentration_panel import ConcentrationPanel
from nexo.ui.components.empty_state import EmptyState
from nexo.ui.financial_formatting import (
    MARKET_HEADERS,
    apply_valuation,
    currency_text,
    market_status,
    money_text,
    position_rows,
    replace_rows,
)
from nexo.ui.pages.assets_page import AssetsPage as AssetsPage  # noqa: PLC0414


class PortfoliosPage(PageContent):
    dialog_requested = Signal(str)
    portfolio_selected = Signal(int)
    refreshed = Signal()

    def __init__(
        self,
        list_portfolios: ListPortfolios,
        load_positions: LoadPortfolioPositions | None = None,
    ) -> None:
        super().__init__("portfolios")
        self._list_portfolios = list_portfolios
        self._load_positions = load_positions
        self._summaries: dict[int, FinancialSummary] = {}
        self._portfolios: list[Portfolio] = []
        self.selected_portfolio_id: int | None = None
        self.selection_buttons: dict[int, QPushButton] = {}
        self.market_labels: dict[int, tuple[QLabel, QLabel, QLabel]] = {}
        actions = QHBoxLayout()
        actions.addWidget(Badge("Carteiras locais"))
        actions.addStretch()
        refresh = QPushButton("Atualizar")
        refresh.setObjectName("SecondaryButton")
        refresh.clicked.connect(self._reload_and_notify)
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
        positions = SectionCard("Posições abertas — carteira selecionada")
        self.positions_table = DataTable(MARKET_HEADERS, [])
        self.positions_table.setObjectName("portfolio_positions_table")
        positions.content.addWidget(self.positions_table)
        self.positions_empty = QLabel(
            "Selecione uma carteira para consultar suas posições."
        )
        positions.content.addWidget(self.positions_empty)
        self.market_feedback = QLabel("Mercado ainda não consultado.")
        self.market_feedback.setWordWrap(True)
        positions.content.addWidget(self.market_feedback)
        self.page_layout.addWidget(positions)
        self.concentration_panel = ConcentrationPanel()
        self.page_layout.addWidget(self.concentration_panel)
        self.page_layout.addStretch()
        self.reload()

    def _reload_and_notify(self) -> None:
        if self.reload():
            self.refreshed.emit()

    def reload(self) -> bool:
        """Replace displayed data only after a successful repository read."""
        try:
            portfolios = self._list_portfolios.execute()
            summaries = (
                {
                    p.id: self._load_positions.summary(p.id)
                    for p in portfolios
                    if p.id is not None
                }
                if self._load_positions is not None
                else {}
            )
        except (
            PortfolioRepositoryError,
            TransactionRepositoryError,
            DomainValidationError,
        ):
            self.feedback.setText(
                "Não foi possível carregar as carteiras. Tente atualizar."
            )
            self.feedback.show()
            return False
        self.feedback.hide()
        self._portfolios = portfolios
        self._summaries = summaries
        self.selection_buttons.clear()
        self.market_labels.clear()
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
        summary = (
            self._summaries.get(portfolio.id) if portfolio.id is not None else None
        )
        if summary is None or summary.transactions_count == 0:
            card.content.addWidget(QLabel("Carteira vazia"))
            metadata = QLabel("0 ativos  •  Sem movimentações")
        else:
            metadata = QLabel(
                f"{summary.positions_count} ativos • {summary.transactions_count} movimentações"
            )
            card.content.addWidget(
                QLabel(f"Capital alocado a custo: {money_text(summary.cost_basis)}")
            )
            card.content.addWidget(
                QLabel(
                    f"Resultado realizado: {money_text(summary.realized_profit_loss)}"
                )
            )
        metadata.setObjectName("SecondaryText")
        card.content.addWidget(metadata)
        if portfolio.id is not None:
            labels = (
                QLabel("Valor atual: —"),
                QLabel("Não realizado: —"),
                QLabel("Resultado total: —"),
            )
            self.market_labels[portfolio.id] = labels
            for label in labels:
                card.content.addWidget(label)
            button = QPushButton("Selecionar")
            button.setObjectName("FilterButton")
            button.setCheckable(True)
            button.setProperty("portfolioId", portfolio.id)
            button.setAccessibleName(
                f"Selecionar {portfolio.name}, carteira {portfolio.id}"
            )
            button.clicked.connect(
                lambda _checked=False, portfolio_id=portfolio.id: self._select(
                    portfolio_id
                )
            )
            self.selection_buttons[portfolio.id] = button
            card.content.addWidget(button)
        return card

    def set_financial_data(
        self, portfolio_id: int | None, result: ReconstructionResult
    ) -> None:
        replace_rows(
            self.positions_table, [row + ("—",) * 4 for row in position_rows(result)]
        )
        self.positions_empty.setVisible(not result.positions)
        self.positions_empty.setText(
            "Nenhuma posição aberta nesta carteira."
            if portfolio_id
            else "Selecione uma carteira para consultar suas posições."
        )

    def set_selected_portfolio(self, portfolio_id: int | None) -> None:
        selected = next((p for p in self._portfolios if p.id == portfolio_id), None)
        self.selected_portfolio_id = selected.id if selected is not None else None
        self.selection_label.setText(
            f"Selecionada: {selected.name}  •  Carteira #{selected.id}"
            if selected is not None
            else "Nenhuma carteira selecionada"
        )
        for identity, button in self.selection_buttons.items():
            checked = identity == self.selected_portfolio_id
            button.setChecked(checked)
            button.setText("Selecionada" if checked else "Selecionar")

    def _select(self, portfolio_id: int) -> None:
        self.set_selected_portfolio(portfolio_id)
        if self.selected_portfolio_id is not None:
            self.portfolio_selected.emit(self.selected_portfolio_id)

    @property
    def portfolio_ids(self) -> tuple[int, ...]:
        return tuple(p.id for p in self._portfolios if p.id is not None)

    def set_market_data(
        self, values: dict[int, PortfolioValuation], selected_id: int | None
    ) -> None:
        for identity, labels in self.market_labels.items():
            valuation = values.get(identity)
            amounts = (
                (
                    valuation.current_market_value,
                    valuation.unrealized_profit_loss,
                    valuation.total_profit_loss,
                )
                if valuation
                else (None, None, None)
            )
            for label, title, amount in zip(
                labels,
                ("Valor atual", "Não realizado", "Resultado total"),
                amounts,
                strict=True,
            ):
                label.setText(f"{title}: {currency_text(amount)}")
                label.setToolTip(
                    market_status(valuation) if valuation else "Sem cotação"
                )
        if selected_id in values:
            value = values[selected_id]
            self.concentration_panel.display(value)
            apply_valuation(self.positions_table, value)
            self.market_feedback.setText(market_status(value))

    def clear_market_data(self, message: str) -> None:
        self.concentration_panel.clear(message)
        for labels in self.market_labels.values():
            for label, title in zip(
                labels, ("Valor atual", "Não realizado", "Resultado total"), strict=True
            ):
                label.setText(f"{title}: —")
        self.market_feedback.setText(message)
