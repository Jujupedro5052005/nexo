from functools import partial
from typing import Any

from PySide6.QtCharts import QChartView
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.domain.interfaces.market_data_provider import (
    MarketCredentialsRequiredError,
    MarketDataError,
)
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.ui.components.asset_analysis_panel import AssetAnalysisPanel
from nexo.ui.components.charts import historical_chart
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.components.market_snapshot_panel import MarketSnapshotPanel
from nexo.ui.financial_formatting import replace_rows
from nexo.ui.workers import TaskRunner


def market_error(error: Exception | None) -> str:
    return (
        str(error)
        if isinstance(error, MarketDataError)
        else "Mercado indisponível. Tente atualizar."
    )


class AssetsPage(PageContent):
    dialog_requested = Signal(str)
    asset_selected = Signal(object)
    integration_requested = Signal()

    def __init__(
        self,
        search_assets: SearchAssets | None = None,
        get_quote: GetAssetQuote | None = None,
        get_history: GetAssetHistory | None = None,
        analyze_asset: AnalyzeAsset | None = None,
    ) -> None:
        super().__init__("assets")
        self._search_assets, self._get_quote, self._get_history = (
            search_assets,
            get_quote,
            get_history,
        )
        self.runner = TaskRunner(self)
        self._search_generation = 0
        self._selection_generation = 0
        self._history_generation = 0
        self.results: tuple[AssetSearchResult, ...] = ()
        self.quote: Quote | None = None
        self.history: PriceHistory | None = None
        self.selected_asset: AssetSearchResult | None = None
        self.chart: QChartView | None = None
        self.page_layout.addWidget(Badge("Dados de mercado • múltiplas fontes"))
        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("asset_search")
        self.search_input.setPlaceholderText("Buscar código ou nome, por exemplo PETR")
        self.search_button = QPushButton("Buscar")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.setEnabled(search_assets is not None)
        self.search_button.clicked.connect(self.search)
        self.search_input.returnPressed.connect(self.search)
        row.addWidget(self.search_input, 1)
        row.addWidget(self.search_button)
        self.page_layout.addLayout(row)
        integration = get_quote.get_integration_status() if get_quote else None
        self.feedback = QLabel(
            "Busque um ativo. "
            + (
                integration.message
                if integration
                else "Consulte Configurações para verificar a integração de mercado."
            )
        )
        self.feedback.setWordWrap(True)
        self.page_layout.addWidget(self.feedback)
        self.table = DataTable(("CÓDIGO", "NOME", "MOEDA", "TIPO"), [])
        self.table.setObjectName("assets_table")
        self.table.itemSelectionChanged.connect(self.select_row)
        self.page_layout.addWidget(self.table)
        self.snapshot_panel = MarketSnapshotPanel()
        self.quote_label = self.snapshot_panel.details
        self.page_layout.addWidget(self.snapshot_panel)
        details = SectionCard("Histórico de preços")
        controls = QHBoxLayout()
        self.period = QComboBox()
        for label, value in (("1 mês", "1mo"), ("3 meses", "3mo"), ("1 ano", "1y")):
            self.period.addItem(label, value)
        self.period.currentIndexChanged.connect(self.refresh_history)
        self.refresh_button = QPushButton("Atualizar ativo")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(lambda: self.refresh_asset(refresh=True))
        controls.addWidget(self.period)
        controls.addWidget(self.refresh_button)
        self.configure_button = QPushButton("Configurar integração")
        self.configure_button.setObjectName("SecondaryButton")
        self.configure_button.clicked.connect(self.integration_requested.emit)
        controls.addWidget(self.configure_button)
        details.content.addLayout(controls)
        self.history_label = QLabel("Histórico indisponível até selecionar um ativo.")
        self.history_label.setWordWrap(True)
        self.history_source_badge = Badge("Histórico: —")
        details.content.addWidget(self.history_source_badge)
        details.content.addWidget(self.history_label)
        self.chart_layout = details.content
        self.page_layout.addWidget(details)
        self.analysis_panel = AssetAnalysisPanel(
            analyze_asset, allow_symbol_entry=False
        )
        self.page_layout.addWidget(self.analysis_panel)
        self.page_layout.addStretch()

    def search(self) -> None:
        case = self._search_assets
        if case is None:
            return
        self._search_generation += 1
        generation = self._search_generation
        query = self.search_input.text().strip()
        self.feedback.setText("Buscando ativos…")
        self.results = ()
        replace_rows(self.table, [])
        self._clear_selection()

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._search_generation:
                return
            if error is not None:
                self.feedback.setText(market_error(error))
                return
            self.results = result
            replace_rows(
                self.table,
                [
                    (r.asset.symbol, r.name, r.currency or "—", r.asset_type)
                    for r in self.results
                ],
            )
            self.feedback.setText(
                f"{len(self.results)} resultados • origem {self.results[0].source}"
                if self.results
                else "Nenhum ativo encontrado."
            )

        self.runner.submit(lambda: case.execute(query), completed)

    def _clear_history(self) -> None:
        self.history = None
        self.history_source_badge.setText("Histórico: —")
        if self.chart is not None:
            self.chart_layout.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def _clear_selection(self) -> None:
        self._selection_generation += 1
        self.selected_asset = None
        self.asset_selected.emit(None)
        self.analysis_panel.set_asset(None, load=False)
        self.quote = None
        self.snapshot_panel.clear()
        self._clear_history()
        self.quote_label.setText("Selecione um resultado para consultar a cotação.")
        self.history_label.setText("Histórico indisponível até selecionar um ativo.")

    def select_row(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.results):
            self.selected_asset = self.results[row]
            self.asset_selected.emit(self.selected_asset.asset)
            self.refresh_asset()

    def refresh_asset(self, *, refresh: bool = False) -> None:
        selected, case = self.selected_asset, self._get_quote
        if selected is None or case is None:
            return
        operation = (
            case.prepare_refresh(selected.asset)
            if refresh
            else partial(case.execute, selected.asset)
        )
        self._selection_generation += 1
        generation = self._selection_generation
        self.quote = None
        self.snapshot_panel.clear()
        self.quote_label.setText(f"{selected.asset.symbol} • Carregando cotação…")

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._selection_generation:
                return
            if error is not None:
                self.quote_label.setText(
                    f"Dados de mercado indisponíveis para {selected.asset.symbol}\nO ativo foi encontrado na busca, mas a consulta detalhada exige autenticação.\n{market_error(error)}"
                    if isinstance(error, MarketCredentialsRequiredError)
                    else f"{selected.asset.symbol} • Preço: — • {market_error(error)}"
                )
                return
            self.quote = result
            quote: Quote = result
            self.snapshot_panel.display(quote)

        self.runner.submit(operation, completed)
        self.refresh_history()
        self.analysis_panel.set_asset(selected.asset)

    def refresh_history(self) -> None:
        selected, case = self.selected_asset, self._get_history
        if selected is None or case is None:
            return
        generation = self._selection_generation
        self._history_generation += 1
        history_generation = self._history_generation
        period = str(self.period.currentData())
        self._clear_history()
        self.history_label.setText("Carregando histórico…")

        def completed(result: Any, error: Exception | None) -> None:
            if (
                generation != self._selection_generation
                or history_generation != self._history_generation
                or period != self.period.currentData()
            ):
                return
            if error is not None:
                self.history_label.setText(market_error(error))
                return
            self.history = result
            history: PriceHistory = result
            self.history_source_badge.setText(f"Histórico: {history.source}")
            self.history_label.setText(
                f"{history.source} • {history.period} • Consultado: {history.retrieved_at.isoformat(timespec='seconds')} • Fechamento informado pela API (pode ser ajustado)."
                if history.points
                else "Nenhum ponto histórico disponível neste período."
            )
            if history.points:
                self.chart = historical_chart(history)
                self.chart_layout.addWidget(self.chart)

        self.runner.submit(lambda: case.execute(selected.asset, period), completed)
