from decimal import Decimal
from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexo.application.analysis.market_research import AnalyzeMarketRisk
from nexo.application.analysis.research_tools import (
    TOOLS,
    EvaluateResearchTool,
    ResearchResult,
)
from nexo.application.analysis.solvency import EvaluateSolvency
from nexo.application.education.checklists import TOPICS, findings
from nexo.domain.errors import DomainValidationError
from nexo.ui.components.common import DataTable, SectionCard, action_button
from nexo.ui.decimal_parser import DecimalInputError, parse_decimal
from nexo.ui.financial_formatting import currency_text, percent_text, replace_rows
from nexo.ui.workers import TaskRunner


def signed_number(text: str) -> Decimal:
    value = text.strip()
    if len(value) > 100:
        raise DecimalInputError("Número muito longo.")
    return (
        -parse_decimal(value[1:], allow_zero=True)
        if value.startswith("-")
        else parse_decimal(value, allow_zero=True)
    )


def show_result(table: DataTable, result: ResearchResult) -> None:
    rows = []
    for label, value, unit, help in result.rows:
        text = (
            "—"
            if value is None
            else percent_text(value)
            if unit == "ratio"
            else currency_text(value)
            if unit == "money"
            else f"{value:.6f}".rstrip("0").rstrip(".")
        )
        rows.append((label + "  ?", text, help))
    replace_rows(table, rows)
    for row, (_, _, _, help) in enumerate(result.rows):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item:
                item.setToolTip(help)


class CalculatorPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Ferramentas de planejamento, valuation e risco")
        self.selector = QComboBox()
        for spec in TOOLS:
            self.selector.addItem(spec.title, spec.key)
        self.content.addWidget(self.selector)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.content.addWidget(self.description)
        self.form = QFormLayout()
        self.content.addLayout(self.form)
        self.inputs: dict[str, QLineEdit] = {}
        self.calculate = action_button("Calcular cenário", True)
        self.calculate.clicked.connect(self.run)
        self.content.addWidget(self.calculate)
        self.feedback = QLabel("Dados manuais; não alteram a carteira.")
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.table = DataTable(
            ("RESULTADO", "VALOR", "COMO INTERPRETAR / PREMISSAS"), []
        )
        self.content.addWidget(self.table)
        self.selector.currentIndexChanged.connect(self.configure)
        self.configure()

    def configure(self) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        self.inputs = {}
        spec = TOOLS[self.selector.currentIndex()]
        self.description.setText(spec.description + "\nReferência: " + spec.reference)
        for field in spec.fields:
            widget = QLineEdit(field.default)
            widget.setToolTip(field.help)
            widget.setAccessibleName(field.label)
            label = QLabel(field.label + "  ?")
            label.setToolTip(field.help)
            label.setBuddy(widget)
            self.form.addRow(label, widget)
            self.inputs[field.key] = widget
            widget.textChanged.connect(lambda: replace_rows(self.table, []))
        replace_rows(self.table, [])
        self.feedback.setText(
            "Cenário com entradas manuais. Taxas devem usar a periodicidade indicada."
        )

    def run(self) -> None:
        spec = TOOLS[self.selector.currentIndex()]
        try:
            values: dict[str, Decimal | tuple[Decimal, ...]] = {}
            for field in spec.fields:
                text = self.inputs[field.key].text()
                if field.kind in {"series", "percent_series"}:
                    value = tuple(signed_number(s) for s in text.split(";"))
                    values[field.key] = (
                        tuple(x / 100 for x in value)
                        if field.kind == "percent_series"
                        else value
                    )
                else:
                    number = signed_number(text)
                    values[field.key] = (
                        number / 100 if field.kind == "percent" else number
                    )
            result = EvaluateResearchTool().execute(spec.key, values)
        except (
            DomainValidationError,
            DecimalInputError,
            ArithmeticError,
            ValueError,
        ) as error:
            replace_rows(self.table, [])
            self.feedback.setText(str(error))
            return
        show_result(self.table, result)
        self.feedback.setText(
            result.explanation
            + " Entradas manuais, sem verificação automática de adequação."
        )


SOLVENCY_FIELDS = (
    ("net_income", "Lucro líquido"),
    ("sales", "Vendas / receita líquida"),
    ("cash", "Disponível"),
    ("permanent_assets", "Ativo permanente • classificação do modelo"),
    ("receivables", "Contas a receber"),
    ("assets", "Ativo total"),
    ("inventory", "Estoques"),
    ("current_liabilities", "Passivo circulante"),
    ("equity", "Patrimônio líquido"),
    ("current_assets", "Ativo circulante"),
    ("long_receivables", "Realizável a longo prazo"),
    ("liabilities", "Exigível total • passivos, não PL"),
    ("bank_debt", "Financiamentos e empréstimos bancários"),
    ("suppliers", "Fornecedores"),
    ("operating_income", "Lucro operacional"),
    ("gross_profit", "Lucro bruto"),
)


class SolvencyPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Insolvência • Elizabetsky, Kanitz e Matias")
        intro = QLabel(
            "Modelos discriminantes históricos, não probabilidades de falência. O artigo fornecido mostra vieses e divergências importantes. Preencha contas da mesma entidade, moeda, escala e período; não misture TTM com trimestre. Referência: Silva & Victor, Quadro 1, pp.5–6."
        )
        intro.setWordWrap(True)
        self.content.addWidget(intro)
        self.nonfinancial = QCheckBox("Confirmei que é empresa não financeira")
        self.aligned = QCheckBox(
            "Conferi bases, período, moeda e classificação das contas"
        )
        self.content.addWidget(self.nonfinancial)
        self.content.addWidget(self.aligned)
        self.source = QLineEdit()
        self.source.setPlaceholderText(
            "Empresa • data do balanço • fonte dos números (obrigatório)"
        )
        self.source.setAccessibleName("Empresa, período e fonte do balanço")
        self.content.addWidget(self.source)
        form = QFormLayout()
        self.inputs = {}
        for key, label in SOLVENCY_FIELDS:
            widget = QLineEdit()
            widget.setPlaceholderText("Deixe vazio se indisponível")
            widget.setAccessibleName(label)
            widget.setToolTip(
                "Valor manual na mesma escala/moeda. Sem estimar contas ausentes. Ativo permanente deve ser reconciliado com a classificação histórica do modelo; ativo não circulante não é substituto automático."
            )
            label_widget = QLabel(label + "  ?")
            label_widget.setToolTip(widget.toolTip())
            label_widget.setBuddy(widget)
            form.addRow(label_widget, widget)
            self.inputs[key] = widget
        self.content.addLayout(form)
        self.calculate = action_button("Comparar os três modelos", True)
        self.calculate.clicked.connect(self.run)
        self.content.addWidget(self.calculate)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.table = DataTable(
            ("MODELO", "ÍNDICE • NÃO É %", "FAIXA / DADOS FALTANTES"), []
        )
        self.content.addWidget(self.table)

        for widget in (*self.inputs.values(), self.source):
            widget.textChanged.connect(self.clear_result)
        self.nonfinancial.toggled.connect(self.clear_result)
        self.aligned.toggled.connect(self.clear_result)

    def clear_result(self) -> None:
        replace_rows(self.table, [])
        self.feedback.setText("Entradas alteradas; calcule novamente.")

    def run(self) -> None:
        try:
            if not self.source.text().strip():
                raise DomainValidationError(
                    "Informe empresa, período e fonte dos dados."
                )
            values = {
                k: signed_number(w.text())
                for k, w in self.inputs.items()
                if w.text().strip()
            }
            results = EvaluateSolvency().execute(
                values,
                nonfinancial=self.nonfinancial.isChecked(),
                aligned=self.aligned.isChecked(),
            )
        except (DomainValidationError, DecimalInputError, ArithmeticError) as error:
            replace_rows(self.table, [])
            self.feedback.setText(str(error))
            return
        replace_rows(
            self.table,
            [
                (
                    r.model + "  ?",
                    f"{r.score:.5f}" if r.score is not None else "—",
                    r.classification
                    + (" • " + ", ".join(r.missing) if r.missing else ""),
                )
                for r in results
            ],
        )
        for row, r in enumerate(results):
            for col in range(3):
                item = self.table.item(row, col)
                if item:
                    item.setToolTip(
                        r.formula
                        + "\nKanitz: >0 solvência; −3 a 0 penumbra/limite; <−3 insolvência. Elizabetsky: corte 0,5. Matias: corte zero. A classificação é do modelo e pode divergir da situação real; não converta o índice em chance de falência."
                    )
        self.feedback.setText(
            "Entrada manual: "
            + self.source.text()
            + ". Resultados não calibrados para prever falência individual; não se faz média dos três índices."
        )


class DiligencePanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Educação financeira e roteiro de diligência")
        self.topic = QComboBox()
        self.topic.addItems(list(TOPICS))
        self.content.addWidget(self.topic)
        self.question_widget = QWidget()
        self.questions = QVBoxLayout(self.question_widget)
        self.content.addWidget(self.question_widget)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.boxes: list[QCheckBox] = []
        self.topic.currentIndexChanged.connect(self.configure)
        self.configure()

    def configure(self) -> None:
        while self.questions.count():
            item = self.questions.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        self.boxes = []
        for label, help in TOPICS[self.topic.currentText()]:
            box = QCheckBox(label)
            box.setToolTip(help)
            box.setAccessibleName(label)
            box.toggled.connect(self.update_findings)
            self.questions.addWidget(box)
            self.boxes.append(box)
        self.update_findings()

    def update_findings(self) -> None:
        selected = tuple(i for i, b in enumerate(self.boxes) if b.isChecked())
        self.feedback.setText(
            "\n\n".join(findings(self.topic.currentText(), selected))
            + "\n\nRoteiro educacional, sem score de fraude, julgamento de empresa ou certificação de adequação. Fontes: PDFs fornecidos de planejamento, análise, mercado, pig butchering e artigo de opinião sobre tesourarias em cripto. Opinião não é norma; criptoativo não é sinônimo de pirâmide."
        )


class MarketRiskPanel(SectionCard):
    def __init__(self, case: AnalyzeMarketRisk | None) -> None:
        super().__init__(
            "Risco de mercado, benchmark e indicadores técnicos • dados reais"
        )
        self.case = case
        self.runner = TaskRunner(self)
        self.generation = 0
        form = QFormLayout()
        self.inputs = {}
        for key, label, default, help in (
            (
                "symbol",
                "Ativo",
                "",
                "Símbolo, ex.: ITSA4. Histórico de um ano consultado apenas ao clicar.",
            ),
            (
                "benchmark",
                "Benchmark de preços",
                "BOVA11",
                "ETF/índice escolhido. Não inclui reinvestimento; moeda deve ser compatível.",
            ),
            (
                "exposure",
                "Exposição monetária na moeda do ativo",
                "",
                "Valor manual em risco; não é lido como patrimônio da carteira.",
            ),
            (
                "confidence",
                "Confiança (%)",
                "95",
                "Entre 50 e 100%. Não indica certeza de perda máxima.",
            ),
            (
                "horizon",
                "Horizonte (pregões)",
                "1",
                "De 1 a 252; exige pelo menos vinte janelas completas.",
            ),
            (
                "rf",
                "Taxa livre de risco anual (%)",
                "0",
                "Premissa explícita para Sharpe/Treynor, mesma moeda do ativo.",
            ),
        ):
            w = QLineEdit(default)
            w.setAccessibleName(label)
            w.setToolTip(help)
            label_widget = QLabel(label + "  ?")
            label_widget.setToolTip(help)
            label_widget.setBuddy(w)
            form.addRow(label_widget, w)
            self.inputs[key] = w
        self.content.addLayout(form)
        self.run_button = action_button("Consultar e calcular", True)
        self.run_button.setEnabled(case is not None)
        self.run_button.clicked.connect(self.run)
        self.content.addWidget(self.run_button)
        self.cancel_button = action_button("Cancelar consulta")
        self.cancel_button.clicked.connect(self.invalidate)
        self.content.addWidget(self.cancel_button)
        self.feedback = QLabel(
            "Sem consulta automática. Todos os valores preservam fonte e janela."
        )
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.table = DataTable(("INDICADOR", "VALOR", "FÓRMULA / USO / LIMITES"), [])
        self.content.addWidget(self.table)
        for widget in self.inputs.values():
            widget.textChanged.connect(self.invalidate)

    def invalidate(self) -> None:
        self.runner.cancel()
        self.run_button.setEnabled(self.case is not None)
        self.generation += 1
        replace_rows(self.table, [])
        self.feedback.setText("Entradas alteradas. Consulte novamente para recalcular.")

    def run(self) -> None:
        if not self.case:
            return
        try:
            exposure = signed_number(self.inputs["exposure"].text())
            confidence = signed_number(self.inputs["confidence"].text()) / 100
            horizon = signed_number(self.inputs["horizon"].text())
            if horizon != horizon.to_integral_value():
                raise DomainValidationError("Horizonte inteiro é necessário.")
            rf = signed_number(self.inputs["rf"].text()) / 100
        except (DecimalInputError, DomainValidationError) as error:
            self.feedback.setText(str(error))
            return
        self.generation += 1
        generation = self.generation
        symbol = self.inputs["symbol"].text()
        benchmark = self.inputs["benchmark"].text()
        case = self.case
        self.run_button.setEnabled(False)
        self.feedback.setText("Consultando histórico e calculando risco…")

        def completed(result: Any, error: Exception | None) -> None:
            self.run_button.setEnabled(True)
            if generation != self.generation:
                return
            if error:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, (DomainValidationError, ValueError))
                    else "Consulta indisponível. Nenhum número foi estimado."
                )
                return
            show_result(self.table, result.result)
            self.feedback.setText(result.source + "\n" + result.result.explanation)

        self.runner.submit(
            lambda: case.execute(
                symbol, benchmark, exposure, confidence, int(horizon), rf
            ),
            completed,
        )


class ResearchWorkbench(QWidget):
    def __init__(self, market: AnalyzeMarketRisk | None = None) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        self.calculators = CalculatorPanel()
        self.solvency = SolvencyPanel()
        self.market = MarketRiskPanel(market)
        self.diligence = DiligencePanel()
        for title, panel in (
            ("Calculadoras", self.calculators),
            ("Mercado e VaR", self.market),
            ("Insolvência", self.solvency),
            ("Diligência / educação", self.diligence),
        ):
            tabs.addTab(panel, title)
        layout.addWidget(tabs)
