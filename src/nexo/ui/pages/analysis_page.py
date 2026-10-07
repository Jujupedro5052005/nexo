from typing import Any

from PySide6.QtCharts import QChartView
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.portfolio.compare_portfolios import (
    ComparedPortfolio,
    ComparePortfolios,
)
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.models.asset import Asset
from nexo.ui.components.asset_analysis_panel import AssetAnalysisPanel
from nexo.ui.components.charts import bar_chart
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.financial_formatting import (
    currency_text,
    decimal_text,
    market_status,
    percent_text,
    replace_rows,
)
from nexo.ui.workers import TaskRunner


class PortfolioComparisonPanel(SectionCard):
    def __init__(
        self,
        list_portfolios: ListPortfolios | None = None,
        compare: ComparePortfolios | None = None,
    ) -> None:
        super().__init__("Comparação de carteiras por ID")
        self._list_portfolios, self._compare = list_portfolios, compare
        self.runner = TaskRunner(self)
        self._generation = 0
        self._catalog: object = None
        self.comparison: tuple[ComparedPortfolio, ...] = ()
        self.chart: QChartView | None = None
        label = QLabel(
            "Selecione duas ou mais carteiras (Ctrl/clique). Nomes iguais são identificados pelo ID."
        )
        label.setWordWrap(True)
        self.content.addWidget(label)
        self.portfolios = QListWidget()
        self.portfolios.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.portfolios.setMaximumHeight(150)
        self.content.addWidget(self.portfolios)
        buttons = QHBoxLayout()
        self.compare_button = QPushButton("Comparar selecionadas")
        self.compare_button.setObjectName("PrimaryButton")
        self.compare_button.clicked.connect(self.compare)
        self.refresh_button = QPushButton("Atualizar comparação")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(lambda: self.compare(refresh=True))
        buttons.addWidget(self.compare_button)
        buttons.addWidget(self.refresh_button)
        self.content.addLayout(buttons)
        self.feedback = QLabel("Selecione pelo menos duas carteiras.")
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.table = DataTable(("MÉTRICA",), [])
        self.content.addWidget(self.table)
        self.positions_table = DataTable(
            ("CARTEIRA / ID", "ATIVO", "VALOR NA MOEDA", "PESO", "DISPONIBILIDADE"), []
        )
        self.content.addWidget(self.positions_table)
        notice = QLabel(
            "Retorno aberto = não realizado / custo das posições abertas. Não é retorno temporal. TWR indisponível sem caixa/fluxos externos e avaliações nos limites de fluxo; XIRR/MWR sem aportes/retiradas; Sharpe sem taxa livre de risco/frequência definidas; benchmark sem série confiável. Sem conversão cambial fictícia."
        )
        notice.setWordWrap(True)
        notice.setObjectName("SecondaryText")
        self.content.addWidget(notice)
        self.portfolios.itemSelectionChanged.connect(self.invalidate)
        self.reload_portfolios()
        self.invalidate()

    def selected_ids(self) -> tuple[int, ...]:
        return tuple(
            int(item.data(Qt.ItemDataRole.UserRole))
            for item in self.portfolios.selectedItems()
        )

    def reload_portfolios(self) -> None:
        if self._list_portfolios is None:
            return
        try:
            rows = self._list_portfolios.execute()
        except PortfolioRepositoryError:
            self.invalidate()
            self.feedback.setText("Não foi possível carregar as carteiras locais.")
            return
        key = tuple((p.id, p.name) for p in rows)
        if key == self._catalog:
            return
        identities = self.selected_ids()
        self._catalog = key
        self.portfolios.blockSignals(True)
        self.portfolios.clear()
        for portfolio in rows:
            if portfolio.id is not None:
                item = QListWidgetItem(f"{portfolio.name} • Carteira #{portfolio.id}")
                item.setData(Qt.ItemDataRole.UserRole, portfolio.id)
                self.portfolios.addItem(item)
                item.setSelected(portfolio.id in identities)
        self.portfolios.blockSignals(False)
        self.invalidate()

    def invalidate(self) -> None:
        self._generation += 1
        self.comparison = ()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["MÉTRICA"])
        replace_rows(self.table, [])
        replace_rows(self.positions_table, [])
        self.compare_button.setEnabled(
            self._compare is not None and len(self.selected_ids()) >= 2
        )
        self.refresh_button.setEnabled(self.compare_button.isEnabled())
        self.feedback.setText(
            "Seleção/contexto alterado; compare pelo menos duas carteiras."
        )
        if self.chart is not None:
            self.content.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def compare(self, *, refresh: bool = False) -> None:
        case, identities = self._compare, self.selected_ids()
        if case is None or len(identities) < 2:
            return
        self.invalidate()
        generation = self._generation
        self.feedback.setText(
            "Carregando ledger e valuation das carteiras selecionadas…"
        )

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._generation or identities != self.selected_ids():
                return
            if error is not None:
                self.feedback.setText(
                    str(error)
                    if isinstance(error, DomainValidationError)
                    else "Comparação indisponível; tente atualizar. Ledger preservado."
                )
                return
            self.comparison = result
            self.display(result)

        self.runner.submit(lambda: case.execute(identities, refresh=refresh), completed)

    def display(self, comparison: tuple[ComparedPortfolio, ...]) -> None:
        self.table.setColumnCount(1 + len(comparison))
        self.table.setHorizontalHeaderLabels(
            ["MÉTRICA"] + [f"{p.name} • #{p.portfolio_id}" for p in comparison]
        )

        def cells(p: ComparedPortfolio) -> tuple[str, ...]:
            v, c = p.valuation, p.valuation.concentration
            return (
                str(len(v.positions)),
                str(p.transactions_count),
                currency_text(v.invested_cost),
                currency_text(v.current_market_value),
                currency_text(v.realized_profit_loss),
                currency_text(v.unrealized_profit_loss),
                currency_text(v.total_profit_loss),
                percent_text(v.unrealized_return),
                percent_text(c.largest),
                percent_text(c.top_three),
                decimal_text(c.hhi) if c.hhi is not None else "—",
            )

        labels = (
            "Posições abertas",
            "Movimentações",
            "Capital alocado a custo (BRL)",
            "Valor atual aberto (BRL)",
            "Resultado realizado (BRL)",
            "Não realizado (BRL)",
            "Resultado total (BRL)",
            "Retorno aberto sobre custo",
            "Maior posição",
            "Top 3 concentração",
            "HHI (Σ pesos²; 1 = um ativo)",
        )
        columns = [cells(p) for p in comparison]
        replace_rows(
            self.table,
            [
                (label, *(column[index] for column in columns))
                for index, label in enumerate(labels)
            ],
        )
        rows: list[tuple[str, ...]] = []
        details = []
        for p in comparison:
            v, c = p.valuation, p.valuation.concentration
            weights = {item.asset: item.weight for item in c.weights}
            details.append(
                f"#{p.portfolio_id}: {market_status(v)}"
                + (
                    f" • Sem valuation BRL: {', '.join(c.unavailable_assets)}"
                    if c.unavailable_assets
                    else ""
                )
            )
            for item in v.positions:
                q = item.quote
                rows.append(
                    (
                        f"{p.name} #{p.portfolio_id}",
                        item.position.asset.symbol,
                        currency_text(item.market_value, q.currency) if q else "—",
                        percent_text(weights.get(item.position.asset)),
                        item.unavailable_reason or "Cotação disponível",
                    )
                )
        replace_rows(self.positions_table, rows)
        self.feedback.setText("\n".join(details))
        complete = [p for p in comparison if p.valuation.complete]
        if complete:
            self.chart = bar_chart(
                [f"{p.name} #{p.portfolio_id}" for p in complete],
                (
                    (
                        "Custo aberto BRL",
                        [float(p.valuation.invested_cost) for p in complete],
                        "#4D7CFF",
                    ),
                    (
                        "Valor atual BRL (valuation completo)",
                        [
                            float(p.valuation.current_market_value)
                            for p in complete
                            if p.valuation.current_market_value is not None
                        ],
                        "#10C7C7",
                    ),
                ),
            )
            self.content.addWidget(self.chart)


class AnalysisPage(PageContent):
    def __init__(
        self,
        analyze_asset: AnalyzeAsset | None = None,
        list_portfolios: ListPortfolios | None = None,
        compare: ComparePortfolios | None = None,
    ) -> None:
        super().__init__("analysis")
        self.page_layout.addWidget(
            Badge("Análises reais • premissas e origem explícitas")
        )
        self.tabs = QTabWidget()
        self.asset_panel = AssetAnalysisPanel(analyze_asset)
        self.comparison_panel = PortfolioComparisonPanel(list_portfolios, compare)
        for title, panel in (
            ("Análise de ativo", self.asset_panel),
            ("Carteiras / comparação", self.comparison_panel),
        ):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(panel)
            self.tabs.addTab(page, title)
        self.page_layout.addWidget(self.tabs)
        self.page_layout.addStretch()

    def set_asset(self, asset: Asset | None) -> None:
        self.asset_panel.set_asset(asset, load=False)

    def load(self) -> None:
        self.comparison_panel.reload_portfolios()
        if (
            self.tabs.currentIndex() == 0
            and self.asset_panel.analysis is None
            and self.asset_panel.symbol_input.text()
        ):
            self.asset_panel.analyze()

    def invalidate_portfolios(self) -> None:
        self.comparison_panel.reload_portfolios()
        self.comparison_panel.invalidate()

    def stop(self) -> None:
        self.asset_panel.runner.stop()
        self.comparison_panel.runner.stop()

    def wait(self) -> None:
        self.asset_panel.runner.wait()
        self.comparison_panel.runner.wait()
