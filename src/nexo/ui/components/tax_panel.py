from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.tax_worksheet import BuildTaxWorksheet
from nexo.calculations.tax import manual_tax_scenario
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.ui.components.common import Badge, DataTable, SectionCard, action_button
from nexo.ui.components.research_workbench import signed_number
from nexo.ui.financial_formatting import currency_text, replace_rows


class TaxPanel(SectionCard):
    def __init__(self, case: BuildTaxWorksheet | None) -> None:
        super().__init__("Assistente de IR de investimentos")
        self.case = case
        self.identity: int | None = None
        self.content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content.addWidget(Badge("Parcial · conferência local e cenário manual"))
        note = QLabel(
            "Consolide vendas e resultado contábil da carteira por mês. Depois simule uma base tributável já conferida. Classes, day trade, isenções e compensações legais exigem revisão; não geramos declaração ou DARF."
        )
        note.setWordWrap(True)
        self.content.addWidget(note)
        self.tabs = QTabWidget()
        self.content.addWidget(self.tabs)
        ledger = QWidget()
        ledger_layout = QVBoxLayout(ledger)
        manual = QWidget()
        manual_layout = QVBoxLayout(manual)
        self.tabs.addTab(ledger, "1 · Conferir operações")
        self.tabs.addTab(manual, "2 · Simular imposto")
        self.year = QSpinBox()
        self.year.setRange(1900, 2200)
        self.year.setValue(datetime.now().astimezone().year)
        self.year.setPrefix("Ano-calendário: ")
        ledger_layout.addWidget(self.year)
        self.load_button = action_button("Consolidar operações locais", True)
        self.load_button.setEnabled(False)
        self.load_button.clicked.connect(self.load)
        ledger_layout.addWidget(self.load_button)
        self.table = DataTable(
            ("MÊS", "VENDAS BRUTAS", "TAXAS PAGAS", "RESULTADO REALIZADO", "ATIVOS"), []
        )
        self.table.setMinimumHeight(180)
        self.table.setMaximumHeight(260)
        ledger_layout.addWidget(self.table)
        self.feedback = QLabel(
            "Escolha uma carteira. O resumo não agrega outras carteiras ou corretoras."
        )
        self.feedback.setWordWrap(True)
        ledger_layout.addWidget(self.feedback)
        form = QFormLayout()
        self.inputs = {}
        for key, label in (
            ("profit", "Resultado tributável conferido (BRL)"),
            ("loss", "Prejuízo compensável anterior (BRL)"),
            ("rate", "Alíquota informada (%)"),
            ("withholding", "IRRF dedutível informado (BRL)"),
        ):
            field = QLineEdit("" if key in {"profit", "rate"} else "0")
            field.setAccessibleName(label)
            form.addRow(label, field)
            self.inputs[key] = field
        manual_layout.addLayout(form)
        calculate = action_button("Simular imposto com minhas premissas")
        calculate.clicked.connect(self.calculate)
        manual_layout.addWidget(calculate)
        self.result = QLabel(
            "Informe resultado, alíquota e compensações da mesma modalidade e período."
        )
        self.result.setWordWrap(True)
        manual_layout.addWidget(self.result)
        manual_layout.addStretch()
        for field in self.inputs.values():
            field.textChanged.connect(
                lambda: self.result.setText("Premissas alteradas. Simule novamente.")
            )
        self.year.valueChanged.connect(self.clear)
        source = QLabel(
            'Apoio didático, não substitui contador ou declaração oficial. <a href="https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1">Receita Federal · renda variável</a>'
        )
        source.setWordWrap(True)
        source.setOpenExternalLinks(True)
        self.content.addWidget(source)

    def set_portfolio(self, identity: int | None) -> None:
        if identity != self.identity:
            self.identity = identity
            self.clear()
        self.load_button.setEnabled(identity is not None and self.case is not None)

    def clear(self) -> None:
        replace_rows(self.table, [])
        self.feedback.setText(
            "Consolide o período selecionado. Resultado contábil não é automaticamente base tributável."
        )
        for key, field in self.inputs.items():
            field.setText("0" if key in {"loss", "withholding"} else "")
        self.result.setText("Informe as premissas do cenário fiscal.")

    def load(self) -> None:
        if not self.case or not self.identity:
            return
        try:
            rows = self.case.execute(self.identity, self.year.value())
            replace_rows(
                self.table,
                [
                    (
                        f"{r.month:02}/{self.year.value()}",
                        currency_text(r.sales),
                        currency_text(r.fees),
                        currency_text(r.realized),
                        ", ".join(r.symbols) or "Sem operações",
                    )
                    for r in rows
                ],
            )
            self.feedback.setText(
                "Resultado realizado pelo preço médio do ledger, com histórico anterior e splits registrados. Taxas pagas não são nova dedução. Sem segregação fiscal automática; exporte o CSV para conferência."
            )
            self.table.setMinimumHeight(180)
            self.table.setMaximumHeight(240)
        except (DomainValidationError, TransactionRepositoryError) as error:
            self.feedback.setText(str(error))

    def calculate(self) -> None:
        try:
            values = {k: signed_number(f.text()) for k, f in self.inputs.items()}
            result = manual_tax_scenario(
                values["profit"],
                values["loss"],
                values["rate"] / 100,
                values["withholding"],
            )
            self.result.setText(
                f"Base após compensação: {currency_text(result.taxable_base)} · imposto estimado: {currency_text(result.estimated_tax)}\nA recolher no cenário: {currency_text(result.payable)} · prejuízo remanescente: {currency_text(result.remaining_loss)}. Confira elegibilidade e regras do período."
            )
        except (ValueError, DomainValidationError) as error:
            self.result.setText(str(error))
