from datetime import datetime
from typing import Any

from PySide6.QtCharts import QChartView
from PySide6.QtCore import QDateTime, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.account import PortfolioAccount
from nexo.application.portfolio.performance import LoadPortfolioPerformance
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.asset import Asset
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.ui.components.charts import line_chart
from nexo.ui.components.common import DataTable, SectionCard, action_button
from nexo.ui.components.research_workbench import signed_number
from nexo.ui.decimal_parser import DecimalInputError
from nexo.ui.financial_formatting import currency_text, percent_text, replace_rows
from nexo.ui.workers import TaskRunner


class AccountPanel(SectionCard):
    changed = Signal(object)

    def __init__(self, case: PortfolioAccount | None) -> None:
        super().__init__("Caixa e eventos • BRL")
        self.case = case
        self.identity: int | None = None
        self.feedback = QLabel(
            "Selecione uma carteira. O caixa legado permanece desconhecido até uma abertura explícita."
        )
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.kind = QComboBox()
        for label, kind in (
            ("Saldo inicial de caixa", "OPENING"),
            ("Aporte externo", "DEPOSIT"),
            ("Retirada externa", "WITHDRAWAL"),
            ("Dividendo recebido", "DIVIDEND"),
            ("JCP recebido", "JCP"),
            ("Taxa avulsa", "FEE"),
            ("Imposto pago", "TAX"),
            ("Desdobramento / grupamento confirmado", "SPLIT"),
        ):
            self.kind.addItem(label, kind)
        self.details = QWidget()
        detail_layout = QVBoxLayout(self.details)
        self.toggle = action_button("Registrar / consultar caixa e eventos")
        self.toggle.setCheckable(True)
        self.toggle.toggled.connect(self.details.setVisible)
        self.content.addWidget(self.toggle)
        self.content.addWidget(self.details)
        self.details.hide()
        form = QFormLayout()
        form.addRow("Evento", self.kind)
        self.amount = QLineEdit("0")
        self.withholding = QLineEdit("0")
        self.symbol = QLineEdit()
        self.ratio = QLineEdit()
        self.note = QLineEdit()
        self.when = QDateTimeEdit(QDateTime.currentDateTime())
        self.when.setCalendarPopup(True)
        self.when.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        for label, widget, help in (
            (
                "Valor bruto BRL ?",
                self.amount,
                "Valor efetivamente liquidado. Abertura pode ser zero; split não movimenta caixa.",
            ),
            (
                "Retenção BRL ?",
                self.withholding,
                "Imposto efetivo retido em dividendo/JCP. Nenhuma alíquota legal é presumida.",
            ),
            (
                "Ativo ?",
                self.symbol,
                "Obrigatório para proventos e desdobramentos; ex.: PETR4.",
            ),
            (
                "Razão de novas / antigas ações ?",
                self.ratio,
                "Somente splits: 2 significa duas novas ações por uma antiga; 0,1 representa grupamento de dez para uma.",
            ),
            (
                "Data da liquidação / evento ?",
                self.when,
                "O saldo inicial representa apenas o caixa nesta data. Compras anteriores não viram aportes. Mesmo instante: abertura, recebimentos, negociações, pagamentos.",
            ),
            (
                "Observação / comprovante",
                self.note,
                "Referência do documento de liquidação. Não inclua dados secretos.",
            ),
        ):
            widget.setToolTip(help)
            widget.setAccessibleName(label)
            label_widget = QLabel(label)
            label_widget.setToolTip(help)
            label_widget.setBuddy(widget)
            form.addRow(label_widget, widget)
        detail_layout.addLayout(form)
        self.save = action_button("Registrar evento confirmado", True)
        self.save.clicked.connect(self.register)
        detail_layout.addWidget(self.save)
        self.table = DataTable(
            (
                "DATA",
                "TIPO",
                "ATIVO",
                "BRUTO BRL",
                "RETENÇÃO BRL",
                "FLUXO EXTERNO BRL",
                "RAZÃO",
                "OBSERVAÇÃO",
            ),
            [],
        )
        self.table.setAccessibleName("Livro de caixa e eventos corporativos")
        detail_layout.addWidget(self.table)
        self.kind.currentIndexChanged.connect(self.configure)
        self.configure()

    def configure(self) -> None:
        kind = self.kind.currentData()
        self.amount.setEnabled(kind != "SPLIT")
        self.ratio.setEnabled(kind == "SPLIT")
        self.symbol.setEnabled(kind in {"SPLIT", "DIVIDEND", "JCP"})
        self.withholding.setEnabled(kind in {"DIVIDEND", "JCP"})

    def set_portfolio(self, identity: int | None) -> None:
        self.identity = identity
        self.save.setEnabled(identity is not None and self.case is not None)
        replace_rows(self.table, [])
        if identity is None or self.case is None:
            self.feedback.setText(
                "Selecione uma carteira para ativar e consultar o caixa."
            )
            return
        try:
            snapshot = self.case.load(identity)
        except (TransactionRepositoryError, DomainValidationError):
            self.feedback.setText(
                "Não foi possível reconstruir o caixa. Nenhum saldo foi estimado."
            )
            return
        cash = snapshot.cash
        self.feedback.setText(
            f"Carteira #{identity} • Caixa: {currency_text(cash.balance)} • Proventos líquidos: {currency_text(cash.income)} • Custos após abertura: {currency_text(cash.costs)}\n"
            + (
                "Caixa não inicializado. Informe saldo e data reais; não há aporte implícito."
                if cash.balance is None
                else f"Ativo desde {cash.opened_at}. Taxas das compras/vendas já são incluídas; não as registre novamente como taxa avulsa."
            )
        )
        replace_rows(
            self.table,
            [
                (
                    e.occurred_at.isoformat(sep=" "),
                    e.kind.value,
                    e.asset.symbol if e.asset else "—",
                    currency_text(e.amount),
                    currency_text(e.withholding),
                    currency_text(e.external_flow),
                    str(e.ratio or "—"),
                    e.note,
                )
                for e in snapshot.events
            ],
        )

    def register(self) -> None:
        if self.case is None or self.identity is None:
            return
        try:
            kind = PortfolioEventType(self.kind.currentData())
            has_asset = kind in {
                PortfolioEventType.SPLIT,
                PortfolioEventType.DIVIDEND,
                PortfolioEventType.JCP,
            }
            event = PortfolioEvent(
                self.identity,
                kind,
                datetime.fromisoformat(
                    self.when.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
                ),
                amount=signed_number(self.amount.text())
                if kind != PortfolioEventType.SPLIT
                else signed_number("0"),
                withholding=signed_number(self.withholding.text())
                if kind in {PortfolioEventType.DIVIDEND, PortfolioEventType.JCP}
                else signed_number("0"),
                asset=Asset(self.symbol.text()) if has_asset else None,
                ratio=signed_number(self.ratio.text())
                if kind == PortfolioEventType.SPLIT
                else None,
                note=self.note.text().strip(),
            )
            saved = self.case.register(event)
        except (
            DomainValidationError,
            DecimalInputError,
            TransactionRepositoryError,
        ) as error:
            self.feedback.setText(str(error))
            return
        self.set_portfolio(self.identity)
        self.changed.emit(saved)


class PerformancePanel(SectionCard):
    def __init__(self, case: LoadPortfolioPerformance | None) -> None:
        super().__init__("Patrimônio histórico e retorno temporal • BRL")
        self.case = case
        self.identity: int | None = None
        self.runner = TaskRunner(self)
        self.generation = 0
        self.chart: QChartView | None = None
        self.feedback = QLabel(
            "Inicialize o caixa em Movimentações. Histórico não é inferido de custo de aquisição."
        )
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.load_button = action_button(
            "Consultar histórico e reconstruir patrimônio", True
        )
        self.load_button.clicked.connect(self.load)
        self.content.addWidget(self.load_button)
        self.cancel_button = action_button("Cancelar consulta")
        self.cancel_button.clicked.connect(lambda: self.set_portfolio(self.identity))
        self.content.addWidget(self.cancel_button)
        self.table = DataTable(
            (
                "DATA",
                "CAIXA BRL",
                "ATIVOS BRL",
                "PATRIMÔNIO BRL",
                "FLUXO EXTERNO BRL",
                "FECHAMENTO MAIS ANTIGO",
            ),
            [],
        )
        self.content.addWidget(self.table)

    def set_portfolio(self, identity: int | None) -> None:
        self.identity = identity
        self.runner.cancel()
        self.generation += 1
        replace_rows(self.table, [])
        self.feedback.setText(
            f"Carteira #{identity}. Consulte para reconstruir caixa + ativos até ontem e calcular TWR diário."
            if identity
            else "Selecione uma carteira."
        )
        self.load_button.setEnabled(identity is not None and self.case is not None)
        if self.chart is not None:
            self.content.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def load(self) -> None:
        case, identity = self.case, self.identity
        if case is None or identity is None:
            return
        self.set_portfolio(identity)
        generation = self.generation
        self.load_button.setEnabled(False)
        self.feedback.setText(
            "Consultando históricos; fechamentos ausentes impedem retorno agregado."
        )

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self.generation:
                return
            self.load_button.setEnabled(True)
            if error:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, DomainValidationError)
                    else "Histórico indisponível. Nenhum retorno foi inventado."
                )
                return
            latest = result.points[-1] if result.points else None
            self.feedback.setText(
                f"TWR diário aproximado: {percent_text(result.twr)} • Último patrimônio: {currency_text(latest.equity if latest else None)}\n{result.convention}\n"
                + "\n".join((*result.sources, *result.issues))
            )
            replace_rows(
                self.table,
                [
                    (
                        str(p.date),
                        currency_text(p.cash),
                        currency_text(p.securities),
                        currency_text(p.equity),
                        currency_text(p.external_flow),
                        str(p.oldest_price_date or "Só caixa"),
                    )
                    for p in result.points
                ],
            )
            if result.points:
                self.chart = line_chart(
                    (
                        (
                            "Patrimônio BRL • datas na tabela",
                            [float(p.equity) for p in result.points],
                            "#10C7C7",
                        ),
                        (
                            "Caixa BRL",
                            [float(p.cash) for p in result.points],
                            "#4D7CFF",
                        ),
                    )
                )
                self.content.addWidget(self.chart)

        self.runner.submit(lambda: case.execute(identity), completed)
