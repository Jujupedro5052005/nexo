from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from nexo.application.portfolio.financial_summary import transaction_amounts
from nexo.domain.models.transaction import Transaction
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.financial_formatting import decimal_text, money_text, replace_rows


class TransactionsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("transactions")
        self._transactions: list[Transaction] = []
        top = QHBoxLayout()
        top.addWidget(Badge("Movimentações locais"))
        top.addStretch()
        self.create_button = QPushButton("+  Nova movimentação")
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(
            lambda: self.dialog_requested.emit("transaction")
        )
        top.addWidget(self.create_button)
        self.page_layout.addLayout(top)
        self.context_label = QLabel("Selecione uma carteira na página Carteiras.")
        self.page_layout.addWidget(self.context_label)
        self.feedback = QLabel()
        self.feedback.setObjectName("WarningBadge")
        self.feedback.hide()
        self.page_layout.addWidget(self.feedback)
        filters = SectionCard("Filtros da carteira selecionada")
        fields = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItem("Todos os tipos", "")
        self.type_filter.addItem("Compra (BUY)", "BUY")
        self.type_filter.addItem("Venda (SELL)", "SELL")
        self.asset_filter = QComboBox()
        self.asset_filter.addItem("Todos os ativos", "")
        self.period_filter = QComboBox()
        self.period_filter.addItems(
            ["Máximo", "Hoje", "7 dias", "Este mês", "3 meses", "6 meses", "1 ano"]
        )
        for combo in (self.type_filter, self.asset_filter, self.period_filter):
            fields.addWidget(combo)
            combo.currentIndexChanged.connect(self.apply_filters)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar ativo")
        self.search.textChanged.connect(self.apply_filters)
        fields.addWidget(self.search)
        filters.content.addLayout(fields)
        self.page_layout.addWidget(filters)
        card = SectionCard("Histórico de movimentações")
        self.table = DataTable(
            (
                "DATA / HORA",
                "TIPO",
                "ATIVO",
                "QUANTIDADE",
                "PREÇO",
                "TAXAS",
                "BRUTO",
                "TOTAL / LÍQUIDO",
            ),
            [],
        )
        self.table.setObjectName("transactions_table")
        card.content.addWidget(self.table)
        self.empty_label = QLabel("Selecione uma carteira para consultar o histórico.")
        card.content.addWidget(self.empty_label)
        unavailable = QLabel(
            "Edição e exclusão de movimentações ainda não estão disponíveis."
        )
        unavailable.setObjectName("SecondaryText")
        card.content.addWidget(unavailable)
        self.page_layout.addWidget(card)
        self.page_layout.addStretch()
        self.set_data(None, [])

    def set_data(
        self, portfolio_id: int | None, transactions: list[Transaction]
    ) -> None:
        self._transactions = transactions
        self.context_label.setText(
            f"Carteira #{portfolio_id}"
            if portfolio_id
            else "Selecione uma carteira na página Carteiras."
        )
        self.create_button.setEnabled(portfolio_id is not None)
        self.feedback.hide()
        self.asset_filter.blockSignals(True)
        self.asset_filter.clear()
        self.asset_filter.addItem("Todos os ativos", "")
        for symbol in sorted({item.asset.symbol for item in transactions}):
            self.asset_filter.addItem(symbol, symbol)
        self.asset_filter.blockSignals(False)
        self.apply_filters()
        if portfolio_id is None:
            self.empty_label.setText(
                "Selecione uma carteira para consultar o histórico."
            )

    def apply_filters(self) -> None:
        if not hasattr(self, "table"):
            return
        today = QDate.currentDate()
        period = self.period_filter.currentText()
        cutoff = {
            "Hoje": today,
            "7 dias": today.addDays(-6),
            "Este mês": QDate(today.year(), today.month(), 1),
            "3 meses": today.addMonths(-3),
            "6 meses": today.addMonths(-6),
            "1 ano": today.addYears(-1),
        }.get(period)
        rows = []
        for item in self._transactions:
            if (
                self.type_filter.currentData()
                and item.transaction_type.value != self.type_filter.currentData()
            ):
                continue
            if (
                self.asset_filter.currentData()
                and item.asset.symbol != self.asset_filter.currentData()
            ):
                continue
            if self.search.text().strip().upper() not in item.asset.symbol:
                continue
            if cutoff is not None and not date(
                cutoff.year(), cutoff.month(), cutoff.day()
            ) <= item.occurred_at.date() <= date(
                today.year(), today.month(), today.day()
            ):
                continue
            gross, settlement = transaction_amounts(item)
            rows.append(
                (
                    item.occurred_at.strftime("%d/%m/%Y %H:%M:%S%z"),
                    item.transaction_type.value,
                    item.asset.symbol,
                    decimal_text(item.quantity),
                    money_text(item.unit_price),
                    money_text(item.fees),
                    money_text(gross),
                    money_text(settlement),
                )
            )
        replace_rows(self.table, rows)
        self.empty_label.setVisible(not rows)
        self.empty_label.setText(
            "Nenhuma movimentação nesta carteira."
            if not self._transactions
            else "Nenhuma movimentação corresponde aos filtros."
        )


from nexo.ui.pages.personal_finance import PlanningPage as PlanningPage  # noqa: PLC0414
