from PySide6.QtWidgets import QComboBox, QFileDialog, QLabel

from nexo.application.portfolio.export_report import ExportReport
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.interfaces.personal_finance_repository import PersonalFinanceError
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.ui.components.common import Badge, PageContent, SectionCard, action_button


class ReportsPage(PageContent):
    def __init__(
        self, listing: ListPortfolios | None = None, export: ExportReport | None = None
    ) -> None:
        super().__init__("reports")
        self.listing, self.export = listing, export
        self.page_layout.addWidget(Badge("Relatórios reais • exportação CSV"))
        card = SectionCard("Exportar dados locais")
        self.kind = QComboBox()
        for label, value in (
            ("Posições e resultado realizado", "positions"),
            ("Histórico de movimentações", "transactions"),
            ("Livro de caixa e eventos corporativos", "events"),
            ("Planejamento financeiro", "planning"),
            ("Metas financeiras", "goals"),
        ):
            self.kind.addItem(label, value)
        self.portfolio = QComboBox()
        self.kind.currentIndexChanged.connect(
            lambda: self.portfolio.setEnabled(
                self.kind.currentData() in {"positions", "transactions", "events"}
            )
        )
        self.generate = action_button("Salvar relatório CSV", True)
        self.generate.setEnabled(export is not None)
        self.generate.clicked.connect(self.save)
        self.feedback = QLabel(
            "CSV com valores exatos do banco local. Posições incluem encerradas; resultado realizado não inclui impostos ou proventos. Planejamento e metas exportam todos os registros. Sem rentabilidade histórica inventada."
        )
        self.feedback.setWordWrap(True)
        for widget in (self.kind, self.portfolio, self.feedback, self.generate):
            card.content.addWidget(widget)
        self.page_layout.addWidget(card)
        self.page_layout.addStretch()
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
