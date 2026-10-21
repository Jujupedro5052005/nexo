import json
from dataclasses import asdict
from decimal import Context, Decimal
from typing import Any

from PySide6.QtCharts import QChartView
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
)

from nexo.application.assets.analyze_asset import AnalyzeAsset, AssetAnalysis
from nexo.calculations.valuation.decision import decision_scenario
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset
from nexo.ui.components.charts import bar_chart
from nexo.ui.components.common import DataTable, SectionCard
from nexo.ui.components.indicator_help import HELP
from nexo.ui.decimal_parser import DecimalInputError, parse_decimal
from nexo.ui.financial_formatting import (
    currency_text,
    percent_text,
    replace_rows,
)
from nexo.ui.workers import TaskRunner


class AssetAnalysisPanel(SectionCard):
    def __init__(
        self,
        analyze_asset: AnalyzeAsset | None = None,
        *,
        allow_symbol_entry: bool = True,
    ) -> None:
        super().__init__("Fundamentos, indicadores e estimativas do ativo")
        self._case = analyze_asset
        self.runner = TaskRunner(self)
        self._generation = 0
        self.analysis: AssetAnalysis | None = None
        self.chart: QChartView | None = None
        controls = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Ticker, ex.: PETR4")
        self.symbol_input.setReadOnly(not allow_symbol_entry)
        self.period = QComboBox()
        for label, data in (("1 mês", "1mo"), ("3 meses", "3mo"), ("1 ano", "1y")):
            self.period.addItem(label, data)
        self.period.setCurrentIndex(2)
        self.yield_input = QLineEdit()
        self.yield_input.setPlaceholderText("Yield requerido (%), ex.: 6")
        self.yield_input.setMaximumWidth(150)
        self.calculate_button = QPushButton("Calcular")
        self.calculate_button.setObjectName("PrimaryButton")
        self.calculate_button.setEnabled(analyze_asset is not None)
        self.calculate_button.clicked.connect(self.analyze)
        self.refresh_button = QPushButton("Atualizar dados")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.setEnabled(analyze_asset is not None)
        self.refresh_button.clicked.connect(lambda: self.analyze(refresh=True))
        for widget in (
            self.symbol_input,
            self.period,
            QLabel("Yield requerido (%)"),
            self.yield_input,
            self.calculate_button,
            self.refresh_button,
        ):
            controls.addWidget(widget)
        self.content.addLayout(controls)
        self.include_jcp = QCheckBox(
            "Incluir JCP bruto nos proventos da janela (sem impostos)"
        )
        self.content.addWidget(self.include_jcp)
        self.include_actions = QCheckBox(
            "Consultar splits/eventos corporativos (consulta adicional)"
        )
        self.content.addWidget(self.include_actions)
        self.include_actions.toggled.connect(self.invalidate)
        self.include_official = QCheckBox(
            "Consultar CVM / demonstrações oficiais (consulta adicional)"
        )
        self.content.addWidget(self.include_official)
        self.include_official.toggled.connect(self.invalidate)
        self.margin_input = QLineEdit("20")
        self.margin_input.setMaximumWidth(100)
        self.margin_input.setToolTip(
            "Desconto exigido sobre o menor teto disponível. Entrada = teto × (1 − margem). De 0 a menos de 100%."
        )
        margin_row = QHBoxLayout()
        margin_label = QLabel("Margem de entrada (%)  ?")
        margin_label.setToolTip(self.margin_input.toolTip())
        margin_row.addWidget(margin_label)
        margin_row.addWidget(self.margin_input)
        margin_row.addStretch()
        self.content.addLayout(margin_row)
        self.margin_input.textChanged.connect(self.invalidate)
        self.scenario_label = QLabel("Cenário de decisão: —")
        self.scenario_label.setWordWrap(True)
        self.scenario_label.setObjectName("AccentText")
        self.scenario_label.setToolTip(
            "O teto conservador é o menor modelo disponível, sem média entre métodos. Entrada aplica sua margem. Revisão usa o teto, não uma previsão de preço. DY de continuidade pressupõe repetir os proventos dos últimos 12 meses."
        )
        self.content.addWidget(self.scenario_label)
        self.feedback = QLabel(
            "Selecione/informe um ativo. Bazin exige yield explícito."
        )
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.indicator_table = DataTable(
            ("INDICADOR", "VALOR", "ORIGEM", "FÓRMULA / BASE"), []
        )
        self.content.addWidget(self.indicator_table)
        self.dividend_label = QLabel("Proventos por ação: —")
        self.dividend_label.setWordWrap(True)
        self.content.addWidget(self.dividend_label)
        self.official_label = QLabel("Dados oficiais: CVM indisponíveis")
        self.official_label.setWordWrap(True)
        self.content.addWidget(self.official_label)
        self.official_toggle = QPushButton("Ver cadastro e demonstrações oficiais")
        self.official_toggle.setObjectName("LinkButton")
        self.official_toggle.setCheckable(True)
        self.content.addWidget(self.official_toggle)
        self.official_details = QPlainTextEdit()
        self.official_details.setReadOnly(True)
        self.official_details.setFixedHeight(220)
        self.official_details.hide()
        self.official_toggle.toggled.connect(self.official_details.setVisible)
        self.content.addWidget(self.official_details)
        self.valuation_table = DataTable(
            ("MODELO", "PREÇO BRL", "DIFERENÇA BRL", "MARGEM", "INTERPRETAÇÃO"), []
        )
        self.content.addWidget(self.valuation_table)
        self.risk_label = QLabel("Risco histórico do ativo: —")
        self.risk_label.setWordWrap(True)
        self.risk_label.setToolTip(HELP["risk"])
        self.content.addWidget(self.risk_label)
        disclaimer = QLabel(
            "Modelos são estimativas, dependem dos dados e premissas e não constituem recomendação financeira. Retorno sobre custo não é performance histórica da carteira."
        )
        disclaimer.setWordWrap(True)
        disclaimer.setObjectName("SecondaryText")
        self.content.addWidget(disclaimer)
        bankruptcy = QLabel(
            "Risco de insolvência / falência  ? — dados insuficientes para Altman Z ou Ohlson O-score"
        )
        bankruptcy.setWordWrap(True)
        bankruptcy.setToolTip(HELP["bankruptcy"])
        self.content.addWidget(bankruptcy)
        self.symbol_input.textChanged.connect(self.invalidate)
        self.yield_input.textChanged.connect(self.invalidate)
        self.period.currentIndexChanged.connect(self.invalidate)
        self.include_jcp.toggled.connect(self.invalidate)

    def invalidate(self) -> None:
        self.runner.cancel()
        self._generation += 1
        self.analysis = None
        self.scenario_label.setText("Cenário de decisão: —")
        replace_rows(self.indicator_table, [])
        replace_rows(self.valuation_table, [])
        self.dividend_label.setText("Proventos por ação: —")
        self.official_label.setText("Dados oficiais: CVM indisponíveis")
        self.official_details.clear()
        self.official_toggle.setChecked(False)
        self.risk_label.setText("Risco histórico do ativo: —")
        self.feedback.setText(
            "Contexto/premissas alterados. Clique Calcular para carregar a análise."
        )
        if self.chart is not None:
            self.content.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def set_asset(self, asset: Asset | None, *, load: bool = True) -> None:
        self.symbol_input.setText(asset.symbol if asset else "")
        self.invalidate()
        if asset is not None and load:
            self.analyze()

    def analyze(self, *, refresh: bool = False, explicit: bool = False) -> None:
        case = self._case
        if case is None:
            return
        try:
            asset = Asset(self.symbol_input.text())
            entry_margin = parse_decimal(self.margin_input.text(), allow_zero=True)
            if entry_margin >= 100:
                raise DecimalInputError("Margem deve ser inferior a 100%.")
            premise = (
                parse_decimal(self.yield_input.text()).scaleb(
                    -2, context=Context(prec=max(50, len(self.yield_input.text()) + 5))
                )
                if self.yield_input.text().strip()
                else None
            )
        except (DomainValidationError, DecimalInputError):
            self.invalidate()
            self.feedback.setText(
                "Informe ticker válido, margem de 0 a menos de 100% e yield positivo em percentual; pode deixar yield vazio para consultar fundamentos/Graham."
            )
            return
        period, include_jcp = (
            str(self.period.currentData()),
            self.include_jcp.isChecked(),
        )
        include_actions = self.include_actions.isChecked()
        include_official = self.include_official.isChecked()
        self.invalidate()
        generation = self._generation
        self.feedback.setText(f"{asset.symbol} • Carregando análise…")

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._generation:
                return
            if error is not None:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, DomainValidationError)
                    else "Análise indisponível. Tente atualizar; ledger local preservado."
                )
                return
            self.analysis = result
            self.display(result)

        self.runner.submit(
            lambda: case.execute(
                asset,
                period=period,
                required_yield=premise,
                include_jcp=include_jcp,
                refresh=refresh,
                include_actions=include_actions,
                include_official=include_official,
                explicit=explicit,
            ),
            completed,
        )

    def display(self, analysis: AssetAnalysis) -> None:
        quote, fundamentals = analysis.quote, analysis.fundamentals
        try:
            entry_margin = parse_decimal(
                self.margin_input.text(), allow_zero=True
            ) / Decimal(100)
            scenario = decision_scenario(
                quote.price if quote and quote.currency == "BRL" else None,
                (analysis.graham.price, analysis.bazin.price),
                analysis.annual_dividend,
                analysis.history,
                entry_margin,
            )
            self.scenario_label.setText(
                f"Cenário de decisão  ?  •  {scenario.reading}\n"
                f"Teto conservador: {currency_text(scenario.ceiling)}  |  Estudar compra até: {currency_text(scenario.entry)}  |  Revisar posição a partir de: {currency_text(scenario.review)}\n"
                f"Variação até o teto (sem prazo): {percent_text(scenario.upside)}  |  DY de continuidade 12M: {percent_text(scenario.dividend_yield)}\n"
                f"Tendência  ?: {scenario.trend}. Não prevê o próximo movimento."
            )
        except (DecimalInputError, ValueError, DomainValidationError):
            self.scenario_label.setText(
                "Margem inválida: informe de 0 a menos de 100%."
            )
        quote_info = (
            f"{currency_text(quote.price, quote.currency)} • {quote.source} • {quote.freshness} • consultado {quote.retrieved_at.isoformat(timespec='seconds')}"
            if quote
            else "Cotação: —"
        )
        fundamental_info = (
            f"Fonte dos fundamentos: {fundamentals.source} • fundamentos consultados {fundamentals.retrieved_at.isoformat(timespec='seconds')} • referência contábil {fundamentals.reference_date or 'não informada'} • dados monetários BRL"
            if fundamentals
            else "Fundamentos: —"
        )
        self.feedback.setText(
            f"{analysis.asset.symbol} • {quote_info}\n{fundamental_info}"
            + ("\n" + " | ".join(analysis.issues) if analysis.issues else "")
        )
        rows = []
        for indicator in analysis.indicators:
            text = (
                currency_text(indicator.value)
                if indicator.unit == "money"
                else percent_text(indicator.value)
                if indicator.unit == "ratio"
                else format(indicator.value, ".2f").replace(".", ",") + "×"
                if indicator.value is not None
                else "—"
            )
            rows.append(
                (
                    indicator.label + "  ?",
                    text,
                    indicator.origin,
                    indicator.reason or indicator.formula,
                )
            )
        replace_rows(self.indicator_table, rows)
        for row, indicator in enumerate(analysis.indicators):
            for column in range(self.indicator_table.columnCount()):
                item = self.indicator_table.item(row, column)
                if item is not None:
                    item.setToolTip(
                        f"{HELP.get(indicator.key, indicator.formula)}\nFórmula/base: {indicator.formula}\nOrigem: {indicator.origin}"
                        + (f"\n{indicator.reason}" if indicator.reason else "")
                    )
        dividend = analysis.dividends
        self.dividend_label.setText(
            f"Proventos selecionados por ação: {currency_text(analysis.annual_dividend)} • política: {'DIVIDENDO + JCP bruto' if analysis.include_jcp else 'somente DIVIDENDO'} • pagamentos {dividend.start_date} a {dividend.end_date} • origem {dividend.source}; consultado {dividend.retrieved_at.isoformat(timespec='seconds')} • futuros e explicitamente não verificados excluídos."
            if dividend
            else "Proventos por ação: — • dados da janela indisponíveis."
        )
        if dividend and dividend.date_basis == "ex_date":
            self.dividend_label.setText(
                f"Proventos: {dividend.source} · fallback • por ação: {currency_text(analysis.annual_dividend)} • data-ex {dividend.start_date} a {dividend.end_date}\n"
                + " | ".join(dividend.limitations)
                + " Bazin usa distribuições de caixa reportadas por data-ex; precisão oficial de tipo/pagamento indisponível."
            )
        official = analysis.official
        self.official_label.setText(
            "Dados oficiais: CVM "
            + (
                "não consultada (opcional)"
                if official is None
                else "disponíveis"
                if official.company
                else "indisponíveis"
            )
            + (
                " · Demonstrações: "
                + "/".join(sorted({r.report_type for r in official.statements}))
                if official and official.statements
                else " · demonstrações indisponíveis"
            )
        )
        self.official_details.setPlainText(
            json.dumps(asdict(official), default=str, ensure_ascii=False, indent=2)
            if official
            else "Sem identidade oficial resolvida."
        )
        # Cross-check is a technical diagnostic, never an adjustment to source values.
        if analysis.diagnostics:
            self.official_details.appendPlainText(
                "\nDiagnóstico técnico:\n" + "\n".join(analysis.diagnostics)
            )
        if analysis.actions:
            self.official_details.appendPlainText(
                "\nSplits externos (ledger preservado):\n"
                + json.dumps(
                    [asdict(a) for a in analysis.actions],
                    default=str,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        valuation_rows = []
        for valuation in (analysis.graham, analysis.bazin):
            margin = valuation.margin
            interpretation = (
                valuation.reason
                if margin is None
                else "Preço abaixo do valor calculado"
                if margin.difference > 0
                else "Preço acima do valor calculado"
                if margin.difference < 0
                else "Preço igual ao valor calculado"
            )
            valuation_rows.append(
                (
                    valuation.name + "  ?",
                    currency_text(valuation.price),
                    currency_text(margin.difference if margin else None),
                    percent_text(margin.ratio if margin else None),
                    interpretation,
                )
            )
        replace_rows(self.valuation_table, valuation_rows)
        for row, valuation in enumerate((analysis.graham, analysis.bazin)):
            for column in range(self.valuation_table.columnCount()):
                item = self.valuation_table.item(row, column)
                if item is not None:
                    item.setToolTip(
                        HELP[valuation.name]
                        + " Margem = (teto − cotação) / teto; diferença = teto − cotação."
                    )
        self.valuation_table.setToolTip(
            f"Graham: sqrt(22,5 × LPA × VPA). Bazin: proventos da janela / yield requerido. Yield aplicado: {percent_text(analysis.required_yield)}."
        )
        risk, history = analysis.risk, analysis.history
        self.risk_label.setText(
            f"Risco do preço do ativo • {history.period if history else 'histórico indisponível'} • {risk.observations} fechamentos • volatilidade diária amostral: {percent_text(risk.daily_volatility)} • anualizada: {percent_text(risk.annual_volatility)} ({risk.trading_days} pregões) • drawdown máximo: {percent_text(risk.max_drawdown)}. {risk.reason}"
            + (
                f" Origem {history.source}; consultado {history.retrieved_at.isoformat(timespec='seconds')}; fechamento informado pode ser ajustado. Não inclui reinvestimento de proventos."
                if history
                else ""
            )
        )
        groups = []
        if quote and quote.currency == "BRL":
            groups.append(
                (
                    "Fechamento diário / EOD"
                    if quote.price_kind == "eod"
                    else "Preço de referência",
                    [float(quote.price)],
                    "#10C7C7",
                )
            )
        for valuation, color in (
            (analysis.graham, "#4D7CFF"),
            (analysis.bazin, "#8B6CFF"),
        ):
            if valuation.price is not None:
                groups.append((valuation.name, [float(valuation.price)], color))
        if groups:
            self.chart = bar_chart([analysis.asset.symbol + " • BRL"], groups)
            self.content.addWidget(self.chart)
