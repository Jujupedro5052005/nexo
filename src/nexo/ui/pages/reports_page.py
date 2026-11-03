from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.export_report import ExportReport
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.tax_worksheet import BuildTaxWorksheet
from nexo.domain.interfaces.personal_finance_repository import PersonalFinanceError
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.ui.components.common import Badge, PageContent, SectionCard, action_button
from nexo.ui.components.tax_panel import TaxPanel


class ReportsPage(PageContent):
    def __init__(
        self,
        listing: ListPortfolios | None = None,
        export: ExportReport | None = None,
        tax: BuildTaxWorksheet | None = None,
    ) -> None:
        super().__init__("reports")
        self.listing, self.export = listing, export
        self.page_layout.addWidget(Badge("Dados locais · exportação e conferência"))
        self.tabs = QTabWidget()
        self.page_layout.addWidget(self.tabs, 1)
        card = SectionCard("Exportar dados locais")
        self.kind = QComboBox()
        for label, value in (
            ("Posições e resultado realizado", "positions"),
            ("Histórico de movimentações", "transactions"),
            ("Livro de caixa e eventos corporativos", "events"),
            ("Planejamento financeiro", "planning"),
            ("Metas financeiras", "goals"),
            ("Conferência mensal para IR (parcial)", "tax"),
        ):
            self.kind.addItem(label, value)
        self.portfolio = QComboBox()
        self.page_layout.insertWidget(1, self.portfolio)
        self.portfolio.setAccessibleName("Carteira para relatórios e conferência de IR")
        self.kind.currentIndexChanged.connect(
            lambda: self.portfolio.setEnabled(
                self.tabs.currentIndex() == 1
                or self.kind.currentData()
                in {"positions", "transactions", "events", "tax"}
            )
        )
        self.generate = action_button("Salvar relatório CSV", True)
        self.generate.setEnabled(export is not None)
        self.generate.clicked.connect(self.save)
        self.feedback = QLabel(
            "CSV com valores exatos do banco local. Posições incluem encerradas; resultado realizado não inclui impostos ou proventos. Planejamento e metas exportam todos os registros. Sem rentabilidade histórica inventada."
        )
        self.feedback.setWordWrap(True)
        for widget in (self.kind, self.feedback, self.generate):
            card.content.addWidget(widget)
        csv_page = QWidget()
        csv_layout = QVBoxLayout(csv_page)
        csv_layout.addWidget(card)
        csv_layout.addStretch()
        self.tabs.addTab(csv_page, "Exportar dados")
        self.tax_panel = TaxPanel(tax)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("PageContent")
        scroll.viewport().setObjectName("PageContent")
        scroll.setWidget(self.tax_panel)
        self.tabs.addTab(scroll, "Assistente de IR")
        self.tabs.currentChanged.connect(
            lambda: self.portfolio.setEnabled(
                self.tabs.currentIndex() == 1
                or self.kind.currentData()
                in {"positions", "transactions", "events", "tax"}
            )
        )
        self.portfolio.currentIndexChanged.connect(
            lambda: self.tax_panel.set_portfolio(self.portfolio.currentData())
        )
        self.tabs.setMinimumHeight(480)
        self.reload()

    def reload(self) -> None:
        if not self.listing:
            return
        selected = self.portfolio.currentData()
        self.portfolio.clear()
        try:
            for portfolio in self.listing.execute():
                self.portfolio.addItem(
                    f"{portfolio.name} • #{portfolio.id}", portfolio.id
                )
            index = self.portfolio.findData(selected)
            if index >= 0:
                self.portfolio.setCurrentIndex(index)
            self.tax_panel.set_portfolio(self.portfolio.currentData())
        except PortfolioRepositoryError as error:
            self.feedback.setText(str(error))

    def save(self) -> None:
        if not self.export:
            return
        path, _selected_filter = QFileDialog.getSaveFileName(
            self, "Salvar relatório", "nexo_relatorio.csv", "CSV (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            if self.kind.currentData() == "tax":
                count = self.export.execute(
                    "tax",
                    self.portfolio.currentData(),
                    path,
                    year=self.tax_panel.year.value(),
                )
            else:
                count = self.export.execute(
                    self.kind.currentData(), self.portfolio.currentData(), path
                )
        except (
            OSError,
            ValueError,
            PersonalFinanceError,
            TransactionRepositoryError,
        ) as error:
            self.feedback.setText(str(error))
        else:
            self.feedback.setText(f"Relatório salvo: {count} registros • {path}")
