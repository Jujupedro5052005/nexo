from collections.abc import Callable
from dataclasses import replace
from datetime import date
from typing import Any, cast

from PySide6.QtCharts import QChartView
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from nexo.application.financial_planning.manage_finances import ManageFinances
from nexo.calculations.projections.planning import goal_projection, monthly_budget
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.personal_finance_repository import PersonalFinanceError
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal, PriceAlert
from nexo.ui.components.charts import bar_chart
from nexo.ui.components.common import (
    Badge,
    DataTable,
    PageContent,
    SectionCard,
    action_button,
)
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.decimal_parser import DecimalInputError, parse_decimal
from nexo.ui.financial_formatting import money_text, percent_text, replace_rows
from nexo.ui.workers import TaskRunner


def date_field(value: date) -> QDateEdit:
    widget = QDateEdit(QDate(value.year, value.month, value.day))
    widget.setCalendarPopup(True)
    widget.setDisplayFormat("dd/MM/yyyy")
    return widget


class RecordDialog(QDialog):
    def __init__(
        self,
        title: str,
        fields: list[tuple[str, Any]],
        save: Callable[[], None],
        changed: Callable[[], None],
        parent: PageContent,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for label, widget in fields:
            form.addRow(label, widget)
        layout.addLayout(form)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.rejected.connect(self.reject)

        def commit() -> None:
            try:
                save()
            except (
                DecimalInputError,
                DomainValidationError,
                PersonalFinanceError,
            ) as error:
                self.feedback.setText(str(error))
                return
            changed()
            self.accept()

        buttons.accepted.connect(commit)
        layout.addWidget(buttons)


class FinancePage(PageContent):
    def __init__(self, key: str, title: str, case: ManageFinances | None) -> None:
        super().__init__(key)
        self.case = case
        self.editor: RecordDialog | None = None
        top = QHBoxLayout()
        top.addWidget(Badge("Dados locais persistidos • independente do ledger"))
        top.addStretch()
        self.add_button = action_button(title, True)
        self.add_button.setEnabled(case is not None)
        top.addWidget(self.add_button)
        self.page_layout.addLayout(top)
        self.feedback = QLabel("Duplo clique em uma linha para editar.")
        self.feedback.setWordWrap(True)
        self.page_layout.addWidget(self.feedback)

    def open_editor(
        self, title: str, fields: list[tuple[str, Any]], save: Callable[[], None]
    ) -> None:
        self.editor = RecordDialog(title, fields, save, self.reload, self)
        self.editor.open()

    def reload(self) -> None:
        raise NotImplementedError


class PlanningPage(FinancePage):
    def __init__(self, case: ManageFinances | None = None) -> None:
        super().__init__("planning", "+ Lançamento", case)
        self.entries: tuple[BudgetEntry, ...] = ()
        self.month = date_field(cast(date, QDate.currentDate().toPython()))
        self.month.setDisplayFormat("MM/yyyy")
        self.month.dateChanged.connect(self.reload)
        self.page_layout.addWidget(self.month)
        row = QHBoxLayout()
        self.metrics = [
            MetricCard(label, "—", tip)
            for label, tip in (
                ("RECEITAS", "Soma dos recebimentos cadastrados no mês selecionado."),
                (
                    "DESPESAS FIXAS",
                    "Soma das despesas fixas cadastradas no mês selecionado.",
                ),
                (
                    "DESPESAS VARIÁVEIS",
                    "Soma das despesas variáveis cadastradas no mês selecionado.",
                ),
                (
                    "CAPACIDADE DE APORTE",
                    "Receitas − despesas. Não desconta uma reserva automática nem movimenta a carteira.",
                ),
            )
        ]
        for metric in self.metrics:
            row.addWidget(metric)
        self.page_layout.addLayout(row)
        self.table = DataTable(("DESCRIÇÃO", "TIPO", "VALOR", "MÊS"), [])
        self.page_layout.addWidget(self.table)
        self.chart_card = SectionCard("Receitas e despesas do mês • BRL")
        self.chart: QChartView | None = None
        self.page_layout.addWidget(self.chart_card)
        self.table.cellDoubleClicked.connect(lambda row, _column: self.edit(row))
        self.add_button.clicked.connect(lambda: self.edit())
        self.reload()

    def reload(self) -> None:
        if not self.case:
            return
        try:
            entries = self.case.budget_entries()
        except PersonalFinanceError as error:
            self.feedback.setText(str(error))
            return
        month = cast(date, self.month.date().toPython())
        self.entries = tuple(
            e
            for e in entries
            if (e.month.year, e.month.month) == (month.year, month.month)
        )
        summary = monthly_budget(entries, month)
        for metric, value in zip(
            self.metrics,
            (summary.income, summary.fixed, summary.variable, summary.available),
            strict=True,
        ):
            metric.set_value(money_text(value), "negative" if value < 0 else "neutral")
        labels = {
            "income": "Receita",
            "fixed": "Despesa fixa",
            "variable": "Despesa variável",
        }
        replace_rows(
            self.table,
            [
                (
                    e.name,
                    labels[e.kind],
                    money_text(e.amount),
                    e.month.strftime("%m/%Y"),
                )
                for e in self.entries
            ],
        )
        if self.chart:
            self.chart_card.content.removeWidget(self.chart)
            self.chart.deleteLater()
        self.chart = bar_chart(
            ["Mês selecionado"],
            (
                ("Receitas", [float(summary.income)], "#3DDC84"),
                ("Despesas", [float(summary.fixed + summary.variable)], "#FF5C6C"),
            ),
        )
        self.chart_card.content.addWidget(self.chart)

    def edit(self, row: int | None = None) -> None:
        if not self.case:
            return
        case = self.case
        entry = self.entries[row] if row is not None else None
        name = QLineEdit(entry.name if entry else "")
        amount = QLineEdit(str(entry.amount) if entry else "")
        kind = QComboBox()
        for label, value in (
            ("Receita", "income"),
            ("Despesa fixa", "fixed"),
            ("Despesa variável", "variable"),
        ):
            kind.addItem(label, value)
        if entry:
            kind.setCurrentIndex(kind.findData(entry.kind))
        month = date_field(
            entry.month if entry else cast(date, self.month.date().toPython())
        )
        self.open_editor(
            "Lançamento do planejamento",
            [
                ("Descrição", name),
                ("Valor (R$)", amount),
                ("Tipo", kind),
                ("Mês de referência", month),
            ],
            lambda: case.save_budget(
                BudgetEntry(
                    name.text(),
                    parse_decimal(amount.text()),
                    kind.currentData(),
                    cast(date, month.date().toPython()),
                    entry.id if entry else None,
                )
            ),
        )


class GoalsPage(FinancePage):
    def __init__(self, case: ManageFinances | None = None) -> None:
        super().__init__("goals", "+ Nova meta", case)
        self.goals: tuple[FinancialGoal, ...] = ()
        self.table = DataTable(
            (
                "META",
                "ACUMULADO  ?",
                "OBJETIVO",
                "PRAZO",
                "PROGRESSO  ?",
                "APORTE MENSAL  ?",
            ),
            [],
        )
        self.table.setToolTip(
            "Progresso = acumulado / objetivo, limitado a 100%. Aporte mensal = saldo restante / meses até o prazo (mínimo um). Cenário sem juros e inflação. Prazo vencido aparece sem aporte calculado. Valores são informados manualmente; não são retirados da carteira."
        )
        self.page_layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(lambda row, _column: self.edit(row))
        self.add_button.clicked.connect(lambda: self.edit())
        self.reload()

    def reload(self) -> None:
        if not self.case:
            return
        try:
            self.goals = self.case.goals()
        except PersonalFinanceError as error:
            self.feedback.setText(str(error))
            return
        rows = []
        for goal in self.goals:
            progress, monthly = goal_projection(
                goal, cast(date, QDate.currentDate().toPython())
            )
            rows.append(
                (
                    goal.name,
                    money_text(goal.current),
                    money_text(goal.target),
                    goal.deadline.strftime("%d/%m/%Y"),
                    percent_text(progress),
                    money_text(monthly) if monthly is not None else "Prazo vencido",
                )
            )
        replace_rows(self.table, rows)

    def edit(self, row: int | None = None) -> None:
        if not self.case:
            return
        case = self.case
        goal = self.goals[row] if row is not None else None
        name = QLineEdit(goal.name if goal else "")
        target = QLineEdit(str(goal.target) if goal else "")
        current = QLineEdit(str(goal.current) if goal else "0")
        deadline = date_field(
            goal.deadline if goal else cast(date, QDate.currentDate().toPython())
        )
        self.open_editor(
            "Meta financeira",
            [
                ("Nome", name),
                ("Objetivo (R$)", target),
                ("Acumulado (R$)", current),
                ("Prazo", deadline),
            ],
            lambda: case.save_goal(
                FinancialGoal(
                    name.text(),
                    parse_decimal(target.text()),
                    parse_decimal(current.text(), allow_zero=True),
                    cast(date, deadline.date().toPython()),
                    goal.id if goal else None,
                )
            ),
        )


class AlertsPage(FinancePage):
    def __init__(self, case: ManageFinances | None = None) -> None:
        super().__init__("alerts", "+ Criar alerta", case)
        self.alerts: tuple[PriceAlert, ...] = ()
        self.runner = TaskRunner(self)
        self.check_button = action_button("Verificar cotações agora")
        self.check_button.setEnabled(case is not None)
        self.check_button.clicked.connect(self.check)
        self.page_layout.addWidget(self.check_button)
        self.table = DataTable(
            (
                "ATIVO",
                "CONDIÇÃO",
                "LIMITE",
                "ATIVO?",
                "ESTADO",
                "CONSULTA / ÚLTIMO DISPARO",
                "COTAÇÃO / FONTE",
            ),
            [],
        )
        self.table.setToolTip(
            "Condições verificadas somente ao clicar Verificar. Preços podem ter atraso. O horário da fonte é preservado; uma condição atingida não afirma que o mercado está negociando agora. Sem envio de notificações externas."
        )
        self.page_layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(lambda row, _column: self.edit(row))
        self.add_button.clicked.connect(lambda: self.edit())
        self.reload()

    def reload(self) -> None:
        if not self.case:
            return
        try:
            self.alerts = self.case.alerts()
        except PersonalFinanceError as error:
            self.feedback.setText(str(error))
            return
        replace_rows(
            self.table,
            [
                (
                    a.symbol,
                    "Até / abaixo" if a.direction == "below" else "A partir / acima",
                    money_text(a.threshold),
                    "Sim" if a.enabled else "Pausado",
                    a.state,
                    f"{a.checked_at or '—'} / {a.triggered_at or '—'}",
                    a.quote_at or "—",
                )
                for a in self.alerts
            ],
        )

    def edit(self, row: int | None = None) -> None:
        if not self.case:
            return
        case = self.case
        alert = self.alerts[row] if row is not None else None
        symbol = QLineEdit(alert.symbol if alert else "")
        threshold = QLineEdit(str(alert.threshold) if alert else "")
        direction = QComboBox()
        direction.addItem("Preço até / abaixo de", "below")
        direction.addItem("Preço a partir / acima de", "above")
        direction.setCurrentIndex(direction.findData(alert.direction) if alert else 0)
        enabled = QCheckBox("Habilitado")
        enabled.setChecked(alert.enabled if alert else True)

        def save() -> None:
            value = PriceAlert(
                symbol.text(),
                parse_decimal(threshold.text()),
                direction.currentData(),
                enabled.isChecked(),
                id=alert.id if alert else None,
            )
            if alert and (alert.symbol, alert.threshold, alert.direction) == (
                value.symbol,
                value.threshold,
                value.direction,
            ):
                value = replace(alert, enabled=enabled.isChecked())
            case.save_alert(value)

        self.open_editor(
            "Alerta de preço",
            [
                ("Ticker B3", symbol),
                ("Condição", direction),
                ("Limite (R$)", threshold),
                ("Estado", enabled),
            ],
            save,
        )

    def check(self) -> None:
        if not self.case:
            return
        self.check_button.setEnabled(False)
        self.feedback.setText("Consultando cotações para os alertas habilitados…")

        def completed(_result: Any, error: Exception | None) -> None:
            self.check_button.setEnabled(True)
            self.feedback.setText(
                "Não foi possível verificar os alertas."
                if error
                else "Verificação concluída. Confira estado, origem e horário da cotação."
            )
            self.reload()

        self.runner.submit(self.case.check_alerts, completed)

    def cancel(self) -> None:
        self.runner.cancel()
        self.check_button.setEnabled(self.case is not None)
        self.feedback.setText(
            "Consulta cancelada. Verifique as cotações novamente quando desejar."
        )
