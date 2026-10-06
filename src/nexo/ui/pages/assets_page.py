from typing import Any

from PySide6.QtCharts import QChartView
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton

from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.domain.interfaces.market_data_provider import MarketDataError
from nexo.domain.models.market_data import AssetSearchResult, PriceHistory, Quote
from nexo.ui.components.charts import historical_chart
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.financial_formatting import currency_text, decimal_text, replace_rows
from nexo.ui.workers import TaskRunner


def market_error(error: Exception | None) -> str:
    return (
        str(error)
        if isinstance(error, MarketDataError)
        else "Mercado indisponível. Tente atualizar."
    )


class AssetsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(
        self,
        search_assets: SearchAssets | None = None,
        get_quote: GetAssetQuote | None = None,
        get_history: GetAssetHistory | None = None,
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
        self.page_layout.addWidget(Badge("Dados de mercado • brapi"))
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
        self.feedback = QLabel(
            "Busque um ativo. Sem token: cotações públicas PETR4, VALE3, ITUB4 e MGLU3."
        )
        self.feedback.setWordWrap(True)
        self.page_layout.addWidget(self.feedback)
        self.table = DataTable(("CÓDIGO", "NOME", "MOEDA", "TIPO"), [])
        self.table.setObjectName("assets_table")
        self.table.itemSelectionChanged.connect(self.select_row)
        self.page_layout.addWidget(self.table)
        details = SectionCard("Cotação do ativo selecionado")
        self.quote_label = QLabel("Selecione um resultado para consultar a cotação.")
        self.quote_label.setWordWrap(True)
        self.quote_label.setObjectName("asset_quote")
        details.content.addWidget(self.quote_label)
        controls = QHBoxLayout()
        self.period = QComboBox()
        for label, value in (("1 mês", "1mo"), ("3 meses", "3mo"), ("1 ano", "1y")):
            self.period.addItem(label, value)
        self.period.currentIndexChanged.connect(self.refresh_history)
        self.refresh_button = QPushButton("Atualizar ativo")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(self.refresh_asset)
        controls.addWidget(self.period)
        controls.addWidget(self.refresh_button)
        details.content.addLayout(controls)
        self.history_label = QLabel("Histórico indisponível até selecionar um ativo.")
        self.history_label.setWordWrap(True)
        details.content.addWidget(self.history_label)
        self.chart_layout = details.content
        self.page_layout.addWidget(details)
        self.page_layout.addStretch()

    def search(self) -> None:
        case = self._search_assets
        if case is None:
            return
        self._search_generation += 1
        generation = self._search_generation
        query = self.search_input.text().strip()
        self.feedback.setText("Buscando na brapi…")
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
                f"{len(self.results)} resultados • origem brapi"
                if self.results
                else "Nenhum ativo encontrado."
            )

        self.runner.submit(lambda: case.execute(query), completed)

    def _clear_history(self) -> None:
        self.history = None
        if self.chart is not None:
            self.chart_layout.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def _clear_selection(self) -> None:
        self._selection_generation += 1
        self.selected_asset = None
        self.quote = None
        self._clear_history()
        self.quote_label.setText("Selecione um resultado para consultar a cotação.")
        self.history_label.setText("Histórico indisponível até selecionar um ativo.")

    def select_row(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self.results):
            self.selected_asset = self.results[row]
            self.refresh_asset()

    def refresh_asset(self) -> None:
        selected, case = self.selected_asset, self._get_quote
        if selected is None or case is None:
            return
        self._selection_generation += 1
        generation = self._selection_generation
        self.quote = None
        self.quote_label.setText(f"{selected.asset.symbol} • Carregando cotação…")

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._selection_generation:
                return
            if error is not None:
                self.quote_label.setText(
                    f"{selected.asset.symbol} • Preço: — • {market_error(error)}"
                )
                return
            self.quote = result
            quote: Quote = result
            timestamp = (
                quote.market_time.isoformat() if quote.market_time else "não informado"
            )
            change = (
                decimal_text(quote.change_percent) + "%"
                if quote.change_percent is not None
                else "—"
            )
            self.quote_label.setText(
                f"{quote.asset.symbol} • {quote.name}\nPreço: {currency_text(quote.price, quote.currency)} • Moeda: {quote.currency} • Variação informada: {change}\nOrigem: {quote.source} • Cotação: {timestamp}\nConsultado: {quote.retrieved_at.isoformat(timespec='seconds')}"
            )

        self.runner.submit(lambda: case.execute(selected.asset), completed)
        self.refresh_history()

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
            self.history_label.setText(
                f"{history.source} • {history.period} • Consultado: {history.retrieved_at.isoformat(timespec='seconds')} • Fechamento informado pela API (pode ser ajustado)."
                if history.points
                else "Nenhum ponto histórico disponível neste período."
            )
            if history.points:
                self.chart = historical_chart(history)
                self.chart_layout.addWidget(self.chart)

        self.runner.submit(lambda: case.execute(selected.asset, period), completed)
