import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from nexo.application.intelligence.tools import encode
from nexo.application.intelligence.workspace import IntelligenceWorkspace
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    AnalysisResponse,
    IntelligenceError,
)
from nexo.ui.components.charts import line_chart
from nexo.ui.components.common import PageContent, SectionCard
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.components.research_workbench import signed_number
from nexo.ui.components.safe_markdown import SafeMarkdownBrowser
from nexo.ui.financial_formatting import currency_text, percent_text
from nexo.ui.workers import TaskRunner


class IntelligencePage(PageContent):
    def __init__(self, workspace: IntelligenceWorkspace | None = None) -> None:
        super().__init__("intelligence")
        self.workspace = workspace
        self.runner = TaskRunner(self)
        self._generation = 0
        self._busy = False
        self._conversation = "default"
        self._response: AnalysisResponse | None = None
        self._transcript: list[str] = []
        self._chart: QWidget | None = None
        self.tabs = QTabWidget()
        self.page_layout.addWidget(self.tabs)
        self._build_chat()
        self._build_library()
        self._build_settings()
        self.page_layout.addStretch()
        self.reload()

    def _build_chat(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        intro = QLabel(
            "Pergunte sobre ativos, consulte sua carteira e explore cenários com cálculos verificáveis."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        row = QHBoxLayout()
        self.conversations = QComboBox()
        self.conversations.currentTextChanged.connect(self._switch_conversation)
        row.addWidget(self.conversations, 1)
        new = QPushButton("Nova conversa")
        new.clicked.connect(self._new_conversation)
        row.addWidget(new)
        layout.addLayout(row)
        context = QFormLayout()
        self.portfolio = QComboBox()
        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("Ex.: ITUB4 · vazio para conversa geral")
        self.method = QComboBox()
        self.method.addItem("Sem valuation", "")
        for identity, name in (
            ("gordon", "Gordon"),
            ("target_yield", "Yield alvo"),
            ("multiples", "Múltiplos"),
        ):
            self.method.addItem(name, identity)
        self.asset_type = QComboBox()
        for identity, name in (
            ("stock", "Ação"),
            ("bank", "Banco"),
            ("insurer", "Seguradora"),
            ("fii", "FII"),
            ("etf", "ETF"),
            ("bond", "Renda fixa"),
            ("crypto", "Cripto"),
        ):
            self.asset_type.addItem(name, identity)
        context.addRow("Carteira (opcional)", self.portfolio)
        context.addRow("Ativo", self.symbol)
        context.addRow("Classe informada", self.asset_type)
        context.addRow("Metodologia", self.method)
        layout.addLayout(context)
        self.premises_panel = QWidget()
        self.premises_layout = QGridLayout(self.premises_panel)
        self.premises_layout.setContentsMargins(0, 0, 0, 0)
        self.premise_fields: dict[str, QLineEdit] = {}
        self.premise_labels: dict[str, QLabel] = {}
        for key, label in (
            ("expected_dividend", "Dividendo esperado / ação (BRL)"),
            ("required_return", "Retorno requerido (%)"),
            ("growth", "Crescimento perpétuo (%)"),
            ("target_yield", "Yield alvo (%)"),
            ("metric_per_share", "Métrica por ação (BRL)"),
            ("reference_multiple", "Múltiplo de referência (vezes)"),
            ("safety_discount", "Desconto de segurança (%)"),
            ("dividend_source", "Origem do dividendo esperado"),
            ("sustainability_note", "Sustentabilidade da distribuição"),
            ("comparability_note", "Justificativa dos comparáveis"),
        ):
            self.premise_fields[key] = QLineEdit(self.premises_panel)
            self.premise_fields[key].setMaxLength(1000)
            self.premise_labels[key] = QLabel(label, self.premises_panel)
        self.premise_fields["safety_discount"].setText("20")
        self.valuation_metric = QComboBox()
        self.valuation_metric.addItem("Lucro por ação · P/L", "eps")
        self.valuation_metric.addItem("Patrimônio por ação · P/VP", "bvps")
        context.addRow("Métrica dos múltiplos", self.valuation_metric)
        self.metric_label = context.labelForField(self.valuation_metric)
        layout.addWidget(self.premises_panel)
        self.advanced = QCheckBox("Usar cenário avançado em JSON")
        self.advanced.setToolTip(
            "Opcional: permite reutilizar um cenário exportado, com taxas em fração."
        )
        layout.addWidget(self.advanced)
        self.assumptions = QPlainTextEdit()
        self.assumptions.setPlaceholderText(
            'Premissas JSON. Taxas em fração e valores decimais entre aspas. Ex.: {"expected_dividend":"3", "target_yield":"0.06", "dividend_source":"premissa manual", "sustainability_note":"cenário informado pelo usuário"}'
        )
        self.assumptions.setMaximumHeight(90)
        self.assumptions.hide()
        self.advanced.toggled.connect(self.assumptions.setVisible)
        self.advanced.toggled.connect(
            lambda checked: self.premises_panel.setEnabled(not checked)
        )
        self.advanced.toggled.connect(
            lambda checked: self.valuation_metric.setEnabled(not checked)
        )
        layout.addWidget(self.assumptions)
        self.method.currentIndexChanged.connect(self._update_premises)
        self._update_premises()
        self.cloud_consent = QCheckBox(
            "Autorizar envio do contexto selecionado ao Gemini"
        )
        layout.addWidget(self.cloud_consent)
        sharing_note = QLabel(
            "Podem ser enviados: pergunta, últimas 4 mensagens resumidas, documentos recuperados e resumo da carteira/ativos selecionados."
        )
        sharing_note.setWordWrap(True)
        sharing_note.setObjectName("SecondaryText")
        layout.addWidget(sharing_note)
        self.chat = SafeMarkdownBrowser()
        self.chat.setMinimumHeight(220)
        self.chat.setOpenLinks(False)
        self.chat.anchorClicked.connect(self._open_source)
        layout.addWidget(self.chat)
        self.question = QPlainTextEdit()
        self.question.setPlaceholderText(
            "Ex.: quais dados faltam para avaliar ITUB4 pelo yield alvo?"
        )
        self.question.setMaximumHeight(64)
        layout.addWidget(self.question)
        actions = QHBoxLayout()
        self.send = QPushButton("Analisar")
        self.send.setObjectName("PrimaryButton")
        self.send.clicked.connect(self.ask)
        self.cancel_button = QPushButton("Interromper")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.export_button = QPushButton("Exportar análise")
        self.export_button.clicked.connect(self._export)
        self.export_button.setEnabled(False)
        for widget in (self.send, self.cancel_button, self.export_button):
            actions.addWidget(widget)
        layout.addLayout(actions)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        self.results = SectionCard("Resultados e memória de cálculo")
        self.metrics = QHBoxLayout()
        self.results.content.addLayout(self.metrics)
        self.evidence = QTextBrowser()
        self.evidence.setMinimumHeight(150)
        self.evidence.setOpenLinks(False)
        self.evidence.anchorClicked.connect(self._open_source)
        self.results.content.addWidget(self.evidence)
        layout.addWidget(self.results)
        self.tabs.addTab(tab, "Conversa e cenários")

    def _update_premises(self) -> None:
        selected = self.method.currentData()
        self._active_premises = {
            "gordon": (
                "expected_dividend",
                "required_return",
                "growth",
                "safety_discount",
                "dividend_source",
                "sustainability_note",
            ),
            "target_yield": (
                "expected_dividend",
                "target_yield",
                "safety_discount",
                "dividend_source",
                "sustainability_note",
            ),
            "multiples": (
                "metric_per_share",
                "reference_multiple",
                "safety_discount",
                "comparability_note",
            ),
        }.get(selected, ())
        for key, field in self.premise_fields.items():
            field.setVisible(key in self._active_premises)
            self.premise_labels[key].setVisible(key in self._active_premises)
        for index, key in enumerate(self._active_premises):
            self.premises_layout.addWidget(
                self.premise_labels[key], index // 2, (index % 2) * 2
            )
            self.premises_layout.addWidget(
                self.premise_fields[key], index // 2, (index % 2) * 2 + 1
            )
        self.premises_panel.setVisible(bool(selected))
        self.valuation_metric.setVisible(selected == "multiples")
        if self.metric_label:
            self.metric_label.setVisible(selected == "multiples")

    def _read_assumptions(self) -> dict[str, Any]:
        if self.advanced.isChecked():
            result = json.loads(self.assumptions.toPlainText() or "{}")
            if not isinstance(result, dict):
                raise ValueError("Use um objeto JSON.")
            return result
        result = {}
        for key in self._active_premises:
            text = self.premise_fields[key].text().strip()
            if not text:
                continue
            if key in {"dividend_source", "sustainability_note", "comparability_note"}:
                result[key] = text
            else:
                number = signed_number(text)
                if key in {
                    "required_return",
                    "growth",
                    "target_yield",
                    "safety_discount",
                }:
                    number /= Decimal(100)
                result[key] = str(number)
        if self.method.currentData() == "multiples":
            result["metric"] = self.valuation_metric.currentData()
        return result

    def _build_library(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        note = QLabel(
            "Documentos autorizados: TXT/Markdown até 200 KB. A busca local é textual; File Search fornece busca semântica quando configurado. Metodologias externas precisam de revisão e não criam código executável."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.sources = QComboBox()
        layout.addWidget(self.sources)
        row = QHBoxLayout()
        for text, callback in (
            ("Importar documento", self._import_document),
            ("Extrair metodologia", self._extract),
            ("Excluir documento local", self._delete_document),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        self.methods = QComboBox()
        self.methods.currentIndexChanged.connect(self._preview_method)
        layout.addWidget(self.methods)
        self.method_preview = QPlainTextEdit()
        self.method_preview.setReadOnly(True)
        self.method_preview.setMinimumHeight(240)
        layout.addWidget(self.method_preview)
        self.reviewer = QLineEdit()
        self.reviewer.setPlaceholderText("Identificação do revisor")
        layout.addWidget(self.reviewer)
        row = QHBoxLayout()
        for text, approve in (("Aprovar versão", True), ("Rejeitar versão", False)):
            button = QPushButton(text)
            button.clicked.connect(
                lambda _checked=False, value=approve: self._review(value)
            )
            row.addWidget(button)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Biblioteca e revisão")

    def _build_settings(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Preencha GEMINI_API_KEY no .env local e reinicie. A chave é lida somente do ambiente e não é exibida. NEXO_AI_PROVIDER=mock força modo offline; NEXO_AI_ENABLED=false desativa o agente. Limites e modelos são configurados no .env.example."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        self.settings_text = QPlainTextEdit()
        self.settings_text.setReadOnly(True)
        self.settings_text.setMinimumHeight(220)
        layout.addWidget(self.settings_text)
        connection = QPushButton("Testar conexão (metadados do modelo)")
        connection.clicked.connect(self._test_connection)
        layout.addWidget(connection)
        clear = QPushButton("Apagar conversas e cache de análises da IA")
        clear.clicked.connect(self._clear_history)
        layout.addWidget(clear)
        layout.addWidget(
            QLabel(
                "Histórico da IA fica em banco separado. Exportação/limpeza do banco financeiro não inclui esse histórico."
            )
        )
        self.tabs.addTab(tab, "Configuração e privacidade")

    @staticmethod
    def _open_source(url: QUrl) -> None:
        if url.scheme() in {"https", "http"}:
            QDesktopServices.openUrl(url)

    def reload(self) -> None:
        if not self.workspace:
            self.send.setEnabled(False)
            self.feedback.setText("NEXO Intelligence indisponível nesta composição.")
            return
        self.portfolio.blockSignals(True)
        selected = self.portfolio.currentData()
        self.portfolio.clear()
        self.portfolio.addItem("Não compartilhar carteira", None)
        for portfolio in self.workspace.portfolios.execute():
            self.portfolio.addItem(f"{portfolio.name} · #{portfolio.id}", portfolio.id)
        self.portfolio.setCurrentIndex(max(0, self.portfolio.findData(selected)))
        self.portfolio.blockSignals(False)
        self.conversations.blockSignals(True)
        self.conversations.clear()
        self.conversations.addItems(
            list(
                dict.fromkeys(
                    (self._conversation, *self.workspace.conversations())
                )
            )
        )
        self.conversations.setCurrentText(self._conversation)
        self.conversations.blockSignals(False)
        self._load_history()
        self.sources.clear()
        for doc in self.workspace.documents():
            self.sources.addItem(
                f"{doc.get('title', doc['id'])} · {doc.get('version', doc.get('status', ''))}",
                doc["id"],
            )
        self.methods.clear()
        for method in self.workspace.methodologies():
            self.methods.addItem(
                f"{method.name} v{method.version} · {method.review_status}",
                (method.methodology_id, method.version),
            )
        self._preview_method()
        self.settings_text.setPlainText(
            json.dumps(self.workspace.status(), ensure_ascii=False, indent=2)
        )
        mode = self.workspace.status()["mode"]
        enabled = self.workspace.status()["enabled"]
        self.send.setEnabled(enabled and not self._busy)
        self.feedback.setText(
            f"Pronto · {mode}. Consultas de mercado usam os providers existentes e seus limites."
            if enabled
            else (
                self.workspace.status().get("configuration_error")
                or "NEXO Intelligence desativado por configuração."
            )
        )

    def _load_history(self) -> None:
        if self.workspace:
            self._transcript = [
                f"### {'Você' if m.role == 'user' else 'NEXO'}\n\n{m.text}"
                for m in self.workspace.history(self._conversation, 30)
            ]
            self.chat.setMarkdown(
                "\n\n---\n\n".join(self._transcript)
                or "### Comece uma análise\n\nEscolha um contexto ou faça uma pergunta. Nenhuma consulta remota ocorre ao abrir esta página."
            )

    def _switch_conversation(self, identity: str) -> None:
        if identity:
            self.cancel()
            self._conversation = identity
            self._load_history()
            self._clear_results()

    def _new_conversation(self) -> None:
        self._switch_conversation(uuid4().hex[:12])
        self.conversations.addItem(self._conversation)
        self.conversations.setCurrentText(self._conversation)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.send.setEnabled(
            not busy
            and self.workspace is not None
            and self.workspace.enabled
        )
        self.cancel_button.setEnabled(busy)
        self.send.setText("Processando…" if busy else "Analisar")

    def ask(self) -> None:
        if not self.workspace or self._busy:
            return
        try:
            assumptions = self._read_assumptions()
            request = AnalysisRequest(
                question=self.question.toPlainText().strip(),
                conversation_id=self._conversation,
                portfolio_id=self.portfolio.currentData(),
                symbol=self.symbol.text().strip().upper(),
                methodology_id=self.method.currentData(),
                asset_type=self.asset_type.currentData(),
                assumptions=assumptions,
                allow_cloud=self.cloud_consent.isChecked(),
            )
        except (ValueError, TypeError):
            self.feedback.setText(
                "Confira pergunta, ticker e premissas. Nos campos, informe percentuais como 6 para 6%; no cenário JSON avançado, use frações como 0.06."
            )
            return
        self._clear_results()
        self._generation += 1
        generation = self._generation
        self._set_busy(True)
        self.feedback.setText("Consultando evidências e preparando a análise…")

        def completed(result: AnalysisResponse | None, error: Exception | None) -> None:
            if generation != self._generation:
                return
            self._set_busy(False)
            if error or result is None:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, IntelligenceError)
                    else "Não foi possível concluir a análise. Revise a configuração e tente novamente."
                )
                return
            self._response = result
            self._load_history()
            self._show_result(result)
            self.feedback.setText(
                f"Concluído · {result.mode} · {result.created_at.isoformat()}"
            )
            self.export_button.setEnabled(True)

        workspace = self.workspace
        self.runner.submit(lambda: workspace.ask(request), completed)

    def _clear_results(self) -> None:
        self._response = None
        self.export_button.setEnabled(False)
        self.evidence.clear()
        while self.metrics.count():
            item = self.metrics.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        if self._chart:
            self.results.content.removeWidget(self._chart)
            self._chart.deleteLater()
            self._chart = None

    def _show_result(self, response: AnalysisResponse) -> None:
        self.evidence.setPlainText(
            json.dumps(
                json.loads(
                    encode(
                        {
                            "financial_tools": response.evidence,
                            "knowledge": response.knowledge,
                        }
                    )
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        for result in response.evidence:
            if result.name != "calculate_valuation" or not result.available:
                continue
            data = result.data
            for title, key in (
                ("Valor teórico (BRL)", "theoretical_value"),
                ("Preço teto (BRL)", "ceiling_price"),
                ("Cotação (BRL)", "quote"),
                ("Margem observada", "safety_margin"),
            ):
                value = Decimal(data[key]) if data.get(key) is not None else None
                formatted = (
                    percent_text(value)
                    if key == "safety_margin"
                    else currency_text(value)
                )
                self.metrics.addWidget(
                    MetricCard(
                        title,
                        formatted,
                        "Cenário condicional · premissas explícitas",
                    )
                )
            points = [p for p in data.get("sensitivity", []) if p["available"]]
            if points:
                chart_view = line_chart(
                    [
                        (
                            "Preço teto · sensibilidade",
                            [float(p["ceiling_price"]) for p in points],
                            "#10C7C7",
                        )
                    ],
                    210,
                )
                self._chart = chart_view
                for axis in chart_view.chart().axes(Qt.Orientation.Horizontal):
                    axis.setTitleText("Ponto de sensibilidade · premissas na tabela")
                for axis in chart_view.chart().axes(Qt.Orientation.Vertical):
                    axis.setTitleText("Preço teto (BRL)")
                self._chart.setToolTip(
                    "Pontos ordenados por premissa: "
                    + ", ".join(str(p["input"]) for p in points)
                    + ". Premissas e valores completos na memória de cálculo."
                )
                self.results.content.addWidget(self._chart)

    def cancel(self) -> None:
        self._generation += 1
        self.runner.cancel()
        self._set_busy(False)
        self.feedback.setText(
            "Interrompido. Respostas atrasadas não serão exibidas; a chamada em curso pode consumir quota até o timeout."
        )

    def _export(self) -> None:
        if self.workspace and self._response:
            name, _ = QFileDialog.getSaveFileName(
                self, "Exportar análise", "nexo-analysis.md", "Markdown (*.md)"
            )
            if name:
                try:
                    self.workspace.export(Path(name), self._response)
                    self.feedback.setText(
                        "Análise exportada com evidências e premissas."
                    )
                except OSError:
                    self.feedback.setText(
                        "Não foi possível salvar a análise no destino."
                    )

    def _import_document(self) -> None:
        if not self.workspace or self._busy:
            return
        name, _ = QFileDialog.getOpenFileName(
            self, "Documento autorizado", "", "Texto (*.txt *.md)"
        )
        if (
            name
            and QMessageBox.question(
                self,
                "Autorização de conteúdo",
                "Você possui autorização para processar e armazenar este documento?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                self.workspace.import_document(Path(name), True)
                self.reload()
            except (OSError, IntelligenceError) as error:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, IntelligenceError)
                    else "Falha ao importar documento."
                )

    def _preview_method(self) -> None:
        if not self.workspace or not hasattr(self, "method_preview"):
            return
        selection = self.methods.currentData()
        method = next(
            (
                m
                for m in self.workspace.methodologies()
                if (m.methodology_id, m.version) == selection
            ),
            None,
        )
        self.method_preview.setPlainText(
            json.dumps(method.model_dump(mode="json"), ensure_ascii=False, indent=2)
            if method
            else ""
        )

    def _review(self, approve: bool) -> None:
        if not self.workspace or self._busy or not self.methods.currentData():
            return
        try:
            identity, version = self.methods.currentData()
            self.workspace.knowledge.review(
                identity, version, approve=approve, reviewer=self.reviewer.text()
            )
            self.reload()
        except IntelligenceError as error:
            self.feedback.setText(str(error))

    def _delete_document(self) -> None:
        if not self.workspace or self._busy or not self.sources.currentData():
            return
        identity = self.sources.currentData()
        try:
            self.workspace.delete_local_document(identity)
        except IntelligenceError as error:
            self.feedback.setText(str(error))
            return
        self.reload()

    def _extract(self) -> None:
        if not self.workspace or self._busy or not self.sources.currentData():
            return
        if self.workspace.cloud and not self.cloud_consent.isChecked():
            self.feedback.setText(
                "Autorize o envio ao Gemini antes de extrair o documento selecionado."
            )
            return
        identity = self.sources.currentData()
        self._run_operation(
            lambda: self.workspace.knowledge.extract(identity),
            "Extração concluída; metodologia pendente de revisão.",
        )

    def _test_connection(self) -> None:
        if self.workspace and not self._busy:
            self._run_operation(
                self.workspace.test_connection, "Teste concluído"
            )

    def _run_operation(self, operation: Any, success: str) -> None:
        self._generation += 1
        generation = self._generation
        self._set_busy(True)
        self.feedback.setText("Processando…")

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._generation:
                return
            self._set_busy(False)
            self.reload()
            self.feedback.setText(
                str(error)
                if isinstance(error, IntelligenceError)
                else (
                    "Operação indisponível."
                    if error
                    else (result if isinstance(result, str) else success)
                )
            )

        self.runner.submit(operation, completed)

    def _clear_history(self) -> None:
        if (
            self.workspace
            and not self._busy
            and QMessageBox.question(
                self,
                "Histórico local da IA",
                "Apagar todas as conversas e o cache de análises? Documentos e contadores de uso serão preservados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.workspace.clear_conversations()
            self._clear_results()
            self.reload()
