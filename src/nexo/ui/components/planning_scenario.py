from decimal import Decimal

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QSpinBox

from nexo.calculations.projections.finance import future_value
from nexo.calculations.projections.planning import allocate_contribution
from nexo.ui.components.common import Badge, SectionCard, action_button
from nexo.ui.components.research_workbench import signed_number
from nexo.ui.financial_formatting import currency_text


class PlanningScenarioPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Simule seus próximos aportes")
        self.content.addWidget(Badge("Simulação manual · não movimenta o patrimônio"))
        note = QLabel(
            "Compare capital inicial, aportes e prazo. A taxa mensal é uma hipótese nominal; não considera inflação, impostos ou custos."
        )
        note.setWordWrap(True)
        self.content.addWidget(note)
        form = QFormLayout()
        self.initial = QLineEdit("0")
        self.payment = QLineEdit("1500")
        self.rate = QLineEdit("0,5")
        self.months = QSpinBox()
        self.months.setRange(1, 600)
        self.months.setValue(36)
        for label, field in (
            ("Capital inicial (BRL)", self.initial),
            ("Aporte no fim do mês (BRL)", self.payment),
            ("Taxa mensal estimada (%)", self.rate),
            ("Prazo em meses", self.months),
        ):
            field.setAccessibleName(label)
            form.addRow(label, field)
        self.content.addLayout(form)
        button = action_button("Projetar cenário", True)
        button.clicked.connect(self.calculate)
        self.content.addWidget(button)
        self.result = QLabel(
            "Ajuste o exemplo e projete para comparar horizontes. Planeje a alocação de acordo com seus objetivos e necessidades de liquidez."
        )
        self.result.setWordWrap(True)
        self.content.addWidget(self.result)
        for field in (self.initial, self.payment, self.rate):
            field.textChanged.connect(
                lambda: self.result.setText("Premissas alteradas. Projete novamente.")
            )
        self.months.valueChanged.connect(
            lambda: self.result.setText("Prazo alterado. Projete novamente.")
        )
        allocation = QFormLayout()
        allocation_note = QLabel(
            "Objetivos de alocação do aporte · exemplo ajustável de 30% / 50% / 20%. Não representa a composição atual da carteira."
        )
        allocation_note.setWordWrap(True)
        self.content.addWidget(allocation_note)
        self.allocation_result = QLabel("Os percentuais devem somar 100%. Ajuste os objetivos e distribua o aporte do cenário.")
        self.allocation_result.setWordWrap(True)
        self.weights = {}
        for title, default in (
            ("Reserva / liquidez (%)", "30"),
            ("Longo prazo (%)", "50"),
            ("Outros objetivos (%)", "20"),
        ):
            field = QLineEdit(default)
            field.setAccessibleName(title)
            self.weights[title] = field
            allocation.addRow(title, field)
            field.textChanged.connect(
                lambda: self.allocation_result.setText(
                    "Alocação alterada. Distribua novamente o aporte."
                )
            )
        self.content.addLayout(allocation)
        distribute = action_button("Distribuir aporte entre meus objetivos")
        distribute.clicked.connect(self.allocate)
        self.content.addWidget(distribute)
        self.content.addWidget(self.allocation_result)
        self.payment.textChanged.connect(
            lambda: self.allocation_result.setText(
                "Aporte alterado. Distribua novamente."
            )
        )

    def allocate(self) -> None:
        try:
            values = allocate_contribution(
                signed_number(self.payment.text()),
                tuple(
                    signed_number(field.text()) / 100 for field in self.weights.values()
                ),
            )
            self.allocation_result.setText(
                "Alocação planejada do aporte: "
                + " · ".join(
                    f"{title.split(' (')[0]}: {currency_text(value)}"
                    for title, value in zip(self.weights, values, strict=True)
                )
                + ". Objetivos manuais, sem compra automática ou sugestão de classes de ativos."
            )
        except ValueError as error:
            self.allocation_result.setText(str(error))

    def calculate(self) -> None:
        try:
            result = future_value(
                signed_number(self.initial.text()),
                signed_number(self.payment.text()),
                signed_number(self.rate.text()) / Decimal(100),
                self.months.value(),
            )
            self.result.setText(
                "Capital projetado: "
                + currency_text(result)
                + ". Hipótese, não previsão de retorno. Compare também com uma taxa menor e um prazo maior."
            )
        except ValueError as error:
            self.result.setText(str(error))
