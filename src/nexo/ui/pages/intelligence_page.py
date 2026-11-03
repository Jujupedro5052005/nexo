import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QResizeEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
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
from nexo.ui.components.chat_composer import ChatComposer
from nexo.ui.components.common import PageContent, SectionCard
from nexo.ui.components.companion import CompanionCard, CompanionState
from nexo.ui.components.intelligence_cards import (
    EvidenceInspector,
    FinancialReportView,
    MethodologyCard,
    structured_text,
)
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.components.research_workbench import signed_number
from nexo.ui.components.safe_markdown import SafeMarkdownBrowser
from nexo.ui.financial_formatting import currency_text, percent_text
from nexo.ui.workers import TaskRunner


class IntelligencePage(PageContent):
    progress_changed = Signal(str)

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
        self._modernize()
        self.progress_changed.connect(self._show_progress)
        if self.workspace:
            self.workspace.orchestrator.progress = self.progress_changed.emit

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
        self.conversations.currentIndexChanged.connect(
            lambda: self._switch_conversation(self.conversations.currentData() or "")
        )
        row.addWidget(self.conversations, 1)
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
        self.question = ChatComposer()
        self.question.submitted.connect(self.ask)
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

    def _modernize(self) -> None:
        context_tab = self.tabs.widget(0)
        assert context_tab is not None
        context_tab.setObjectName("PageContent")
        self.tabs.removeTab(0)
        chat_tab = QWidget()
        root = QVBoxLayout(chat_tab)
        root.setContentsMargins(0, 6, 0, 0)
        self.companion = CompanionCard()
        self.companion.help_requested.connect(self._guide)
        self.companion.hide()
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Conversa"))
        self.conversations.setMaximumWidth(190)
        toolbar.addWidget(self.conversations, 1)
        new = QPushButton("Nova conversa")
        new.clicked.connect(self._new_conversation)
        toolbar.addWidget(new)
        toolbar.addWidget(QLabel("Carteira"))
        toolbar.addWidget(self.portfolio, 2)
        self.provider_label = QLabel()
        self.provider_label.setObjectName("AccentText")
        toolbar.addWidget(self.provider_label)
        toggle = QPushButton("Contexto e preferências")
        self.context_toggle = toggle
        toggle.setCheckable(True)
        toggle.hide()
        options = QPushButton("Opções")
        menu = QMenu(options)
        menu.addAction("Configuração", self._open_settings)
        menu.addAction("Biblioteca e fontes", lambda: self.tabs.setCurrentIndex(2))
        menu.addAction("Detalhes técnicos", self._inspect)
        options.setMenu(menu)
        toolbar.addWidget(options)
        root.addLayout(toolbar)
        self.chat_splitter = QSplitter(Qt.Orientation.Horizontal)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        suggestions = QHBoxLayout()
        for label, question, deep in (
            (
                "Analisar minha carteira",
                "Analise toda a minha carteira e identifique as melhores oportunidades nas condições atuais.",
                True,
            ),
            (
                "Analisar um ativo",
                "Analise PETR4 considerando o preço atual e minha posição.",
                True,
            ),
            ("Calcular preço teto", "Qual é o preço teto de PETR4?", True),
        ):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, q=question, d=deep: self._suggest(q, d)
            )
            suggestions.addWidget(button)
        layout.addLayout(suggestions)
        self.chat.setMinimumHeight(220)
        layout.addWidget(self.chat, 1)
        self.question.setPlaceholderText(
            "Pergunte ao Nexo… Enter envia · Shift+Enter cria uma linha"
        )
        self.question.setMaximumHeight(76)
        layout.addWidget(self.question)
        self.cloud_consent.setText(
            "Permitir que Gemini use a pergunta e os dados selecionados"
        )
        layout.addWidget(self.cloud_consent)
        self.cloud_consent.setVisible(
            bool(self.workspace and self.workspace.orchestrator.cloud)
        )
        actions = QHBoxLayout()
        self.report_button = QPushButton("Ver análise completa")
        self.report_button.setEnabled(False)
        self.report_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        for button in (self.send, self.cancel_button, self.report_button):
            actions.addWidget(button)
        self.cancel_button.hide()
        self.send.setText("Enviar")
        layout.addLayout(actions)
        layout.addWidget(self.feedback)
        self.chat_splitter.addWidget(body)
        self.context_drawer = QScrollArea()
        self.context_drawer.setWidgetResizable(True)
        self.context_drawer.viewport().setObjectName("PageContent")
        self.context_drawer.setWidget(context_tab)
        self.context_drawer.setMinimumWidth(0)
        self.context_drawer.setObjectName("PageContent")
        self.context_dialog = QDialog(self)
        self.context_dialog.setWindowTitle("Contexto e preferências da análise")
        self.context_dialog.setObjectName("PageContent")
        self.context_dialog.resize(720, 630)
        self.context_dialog.setMinimumSize(580, 420)
        dialog_layout = QVBoxLayout(self.context_dialog)
        dialog_layout.addWidget(self.context_drawer)
        close_context = QPushButton("Voltar à conversa")
        close_context.clicked.connect(self.context_dialog.close)
        dialog_layout.addWidget(close_context)
        self.context_drawer.hide()
        toggle.toggled.connect(self._toggle_context)
        self.context_dialog.finished.connect(lambda: toggle.setChecked(False))
        self.chat_splitter.setStretchFactor(0, 1)
        root.addWidget(self.chat_splitter, 1)
        self.tabs.insertTab(0, chat_tab, "Copiloto")
        self.tabs.setCurrentIndex(0)
        self.deep_mode = QCheckBox("Análise aprofundada de todos os ativos")
        self.estimate_consent = QCheckBox(
            "Usar cenários estimados, identificados e revisáveis"
        )
        self.estimate_consent.setChecked(True)
        context_layout = cast(QVBoxLayout, context_tab.layout())
        context_layout.insertWidget(0, self.estimate_consent)
        context_layout.insertWidget(0, self.deep_mode)
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        self.report_view = FinancialReportView()
        self.report_view.show_report({})
        report_layout.addWidget(self.report_view)
        report_layout.addWidget(self.results)
        report_layout.addWidget(self.export_button)
        self.results.hide()
        self.evidence.hide()
        self.tabs.insertTab(1, report_tab, "Relatório financeiro")
        self.method_preview.hide()
        self.method_card_host = QWidget()
        self.method_card_layout = QVBoxLayout(self.method_card_host)
        library_tab = self.tabs.widget(2)
        assert library_tab is not None
        cast(QVBoxLayout, library_tab.layout()).insertWidget(3, self.method_card_host)
        self.source_preview = SafeMarkdownBrowser()
        self.source_preview.setMinimumHeight(300)
        self.source_preview.setOpenLinks(False)
        self.source_preview.anchorClicked.connect(self._open_source)
        cast(QVBoxLayout, library_tab.layout()).addWidget(self.source_preview)
        self.sources.currentIndexChanged.connect(self._preview_source)
        self.source_search = QLineEdit()
        self.source_search.setPlaceholderText(
            "Pesquisar documentos e fontes por título…"
        )
        self.source_search.textChanged.connect(self._filter_sources)
        cast(QVBoxLayout, library_tab.layout()).insertWidget(1, self.source_search)
        self.settings_text.hide()
        self.status_summary = QLabel()
        self.status_summary.setWordWrap(True)
        self.status_summary.setObjectName("SectionTitle")
        settings_tab = self.tabs.widget(3)
        assert settings_tab is not None
        cast(QVBoxLayout, settings_tab.layout()).insertWidget(1, self.status_summary)
        self._refresh_visuals()
        self.portfolio.currentIndexChanged.connect(
            lambda: self._context_changed(reset_conversation=True)
        )
        self.symbol.textChanged.connect(self._context_changed)
        for index in (1, 2, 3):
            content = self.tabs.widget(index)
            assert content is not None
            content.setObjectName("PageContent")
            title = self.tabs.tabText(index)
            self.tabs.removeTab(index)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.viewport().setObjectName("PageContent")
            scroll.setWidget(content)
            self.tabs.insertTab(index, scroll, title)
        self.tabs.setCurrentIndex(0)
        self.tabs.tabBar().hide()
        self.back_button = QPushButton("Voltar à conversa")
        self.back_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.back_button.hide()
        self.page_layout.insertWidget(0, self.back_button)
        self.tabs.currentChanged.connect(
            lambda index: self.back_button.setVisible(index != 0)
        )
        if self.workspace:
            status = self.workspace.status()
            self.provider_label.setText(status.get("provider_note", status["mode"]))

    def _open_settings(self) -> None:
        window = self.window()
        if hasattr(window, "show_page"):
            window.show_page(10)
        else:
            self.tabs.setCurrentIndex(3)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "chat_splitter"):
            QTimer.singleShot(0, self._fit_tabs)

    def _fit_tabs(self) -> None:
        self.chat.setMinimumHeight(180 if self.viewport().width() < 1000 else 220)
        self.tabs.setFixedHeight(
            max(440, self.viewport().height() - self.tabs.y() - 24)
        )

    def _filter_sources(self, text: str) -> None:
        if not self.workspace:
            return
        self.sources.clear()
        for doc in self.workspace.documents():
            if text.casefold() in doc.get("title", "").casefold():
                self.sources.addItem(doc.get("title", doc["id"]), doc["id"])
        self._preview_source()

    def _preview_source(self) -> None:
        if not self.workspace or not hasattr(self, "source_preview"):
            return
        doc = next(
            (
                d
                for d in self.workspace.documents()
                if d["id"] == self.sources.currentData()
            ),
            None,
        )
        if doc:
            text = (
                doc.get("text")
                or f"### {doc.get('title', '')}\n\nReferência audiovisual · {doc.get('uri', '')}\n\nAutorização: {'registrada' if doc.get('authorized') else 'não concedida'} · estado {doc.get('status')}\n\nData: {doc.get('published_at') or 'não confirmada'} · duração: {doc.get('duration') or 'não confirmada'}.\n\nMetodologias: somente hipóteses de tema, sem extração confirmada."
            )
            self.source_preview.setMarkdown(text)
        else:
            self.source_preview.clear()

    def _suggest(self, question: str, deep: bool) -> None:
        self.question.setPlainText(question)
        self.deep_mode.setChecked(deep)
        if deep and not self.portfolio.currentData() and not self.symbol.text().strip():
            self.feedback.setText(
                "Selecione uma carteira ou escreva o ticker na pergunta e envie."
            )
        self.question.setFocus()

    def _show_progress(self, text: str) -> None:
        if self._busy:
            self.feedback.setText(text)
            self.companion.set_state(CompanionState.ANALYZING, text)

    def _toggle_context(self, visible: bool) -> None:
        self.context_drawer.setVisible(visible)
        if visible:
            self.context_dialog.show()
            self.context_dialog.raise_()
        else:
            self.context_dialog.hide()

    def _guide(self) -> None:
        self.companion.set_state(
            CompanionState.EXPLAINING,
            "1. Abra Contexto e selecione a carteira. 2. Escolha Analisar carteira. 3. Consulte o Relatório e revise as premissas. Para conceitos, basta perguntar.",
        )

    def explain_topic(self, topic: str) -> None:
        self.question.setPlainText(
            "Explique de forma didática "
            + topic
            + ", com um exemplo e cuidados para iniciantes."
        )
        self.tabs.setCurrentIndex(0)
        self.companion.set_state(
            CompanionState.EXPLAINING,
            "Preparei sua pergunta. Envie para receber a explicação; o contexto só vai ao Gemini com sua autorização.",
        )

    def _context_changed(self, *, reset_conversation: bool = False) -> None:
        if self._busy:
            self.cancel()
        self._clear_results()
        if reset_conversation:
            draft = self.question.toPlainText()
            self._new_conversation()
            self.question.setPlainText(draft)
        if hasattr(self, "context_toggle"):
            name = self.portfolio.currentText()
            self.context_toggle.setText(
                "Contexto · "
                + (
                    name.split(" · ")[0]
                    if self.portfolio.currentData()
                    else (self.symbol.text() or "sem carteira")
                )
            )

    def _inspect(self) -> None:
        payload = (
            self._response.model_dump(mode="json")
            if self._response
            else (self.workspace.status() if self.workspace else {})
        )
        dialog = EvidenceInspector(structured_text(payload), self)
        if self.workspace and self._response:
            export = QPushButton("Exportar diagnóstico estruturado")

            def save_diagnostics() -> None:
                name, _ = QFileDialog.getSaveFileName(
                    dialog,
                    "Exportar diagnóstico",
                    "nexo-diagnostic.json",
                    "JSON (*.json)",
                )
                if name and self.workspace and self._response:
                    try:
                        self.workspace.export_diagnostics(Path(name), self._response)
                    except OSError:
                        self.feedback.setText("Não foi possível salvar o diagnóstico.")

            export.clicked.connect(save_diagnostics)
            cast(QVBoxLayout, dialog.layout()).insertWidget(1, export)
        dialog.exec()

    def _refresh_visuals(self) -> None:
        if not self.workspace or not hasattr(self, "status_summary"):
            return
        status = self.workspace.status()
        usage = status["usage"]
        self.status_summary.setText(
            f"{status['mode']} · {status['model']}\nChave: {'configurada' if status['key_configured'] else 'não configurada'}\nRequisições: {usage['requests']} / {status['daily_request_limit']} · tokens contabilizados: {usage['tokens_accounted']} / {status['daily_token_limit']}\nBiblioteca: {len(self.workspace.documents())} documentos · {status['file_search']}\nPrivacidade: contexto enviado somente com a permissão marcada no painel."
        )
        self._preview_method()
        self._preview_source()

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
        for index, identity in enumerate(
            dict.fromkeys((self._conversation, *self.workspace.conversations()))
        ):
            messages = self.workspace.history(identity, 2)
            title = next(
                (m.text.replace("\n", " ")[:44] for m in messages if m.role == "user"),
                "Conversa principal" if identity == "default" else "Nova conversa",
            )
            self.conversations.addItem(f"{index + 1} · {title}", identity)
        self.conversations.setCurrentIndex(
            self.conversations.findData(self._conversation)
        )
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
        self._refresh_visuals()
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
                or "Olá! Sou o Nexo, seu assistente de análise de investimentos. Posso analisar um ativo, explorar sua carteira ou explicar uma estratégia. O que gostaria de investigar?"
            )

    def _switch_conversation(self, identity: str) -> None:
        if identity:
            if self._busy:
                self.cancel()
            else:
                self._generation += 1
                self.runner.cancel()
            self._conversation = identity
            self._load_history()
            self._clear_results()
            self.feedback.setText(
                "Conversa pronta. Escolha uma sugestão ou escreva sua pergunta."
            )
            if hasattr(self, "companion"):
                self.companion.set_state(
                    CompanionState.READY,
                    "Vamos começar. Seu contexto permanece selecionado; nenhuma análise é enviada automaticamente.",
                )

    def _new_conversation(self) -> None:
        self.context_toggle.setChecked(False)
        identity = uuid4().hex[:12]
        self.conversations.addItem(
            f"{self.conversations.count() + 1} · Nova conversa", identity
        )
        self.conversations.setCurrentIndex(self.conversations.findData(identity))
        self.question.clear()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.send.setEnabled(
            not busy and self.workspace is not None and self.workspace.enabled
        )
        self.cancel_button.setEnabled(busy)
        self.cancel_button.setVisible(busy)
        self.send.setText("Processando…" if busy else "Enviar")
        if hasattr(self, "companion"):
            self.companion.set_state(
                CompanionState.ANALYZING if busy else CompanionState.READY,
                "Consultando evidências e preparando cenários…"
                if busy
                else "Você pode continuar a conversa ou explorar o relatório.",
            )

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
                analysis_mode="deep"
                if hasattr(self, "deep_mode") and self.deep_mode.isChecked()
                else "chat",
                allow_estimates=self.estimate_consent.isChecked()
                if hasattr(self, "estimate_consent")
                else True,
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
                self.companion.set_state(
                    CompanionState.ALERT,
                    "A análise precisa de atenção. Confira a mensagem e ajuste o contexto antes de tentar novamente.",
                )
                self.feedback.setText(
                    str(error)
                    if isinstance(error, IntelligenceError)
                    else "Não foi possível concluir a análise. Revise a configuração e tente novamente."
                )
                self.send.setText("Tentar novamente")
                return
            self._response = result
            self.companion.set_state(
                CompanionState.COMPLETE,
                "Análise pronta. Veja o relatório, revise as fontes ou peça outra margem de segurança.",
            )
            self._load_history()
            self._show_result(result)
            if hasattr(self, "report_view"):
                self.report_view.show_report(result.report)
            self.feedback.setText(
                "Gemini · resposta concluída"
                if result.mode == "gemini"
                else "Consulta local concluída · interpretação Gemini não utilizada"
            )
            self.export_button.setEnabled(True)
            self.report_button.setEnabled(
                bool(result.report or result.evidence or result.knowledge)
            )

        workspace = self.workspace
        self.runner.submit(lambda: workspace.ask(request), completed)

    def _clear_results(self) -> None:
        self._response = None
        self.export_button.setEnabled(False)
        if hasattr(self, "report_button"):
            self.report_button.setEnabled(False)
        self.evidence.clear()
        self.results.hide()
        if hasattr(self, "report_view"):
            self.report_view.show_report({})
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
        self.results.setVisible(
            any(
                r.name == "calculate_valuation" and r.available
                for r in response.evidence
            )
        )
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
        if hasattr(self, "method_card_layout"):
            while self.method_card_layout.count():
                item = self.method_card_layout.takeAt(0)
                widget = item.widget() if item else None
                if widget:
                    widget.deleteLater()
            if method:
                self.method_card_layout.addWidget(MethodologyCard(method))

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
            self._run_operation(self.workspace.test_connection, "Teste concluído")

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
