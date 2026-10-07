from PySide6.QtCharts import QChartView
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.ui.components.charts import allocation_donut
from nexo.ui.components.common import DataTable, SectionCard
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.components.responsive_pair import ResponsivePair
from nexo.ui.financial_formatting import (
    currency_text,
    decimal_text,
    percent_text,
    replace_rows,
)


class ConcentrationPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Concentração por ativo — posições abertas BRL")
        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.metrics = {
            "largest": MetricCard("MAIOR POSIÇÃO", "—", "Participação no valor aberto"),
            "top_three": MetricCard("TOP 3 POSIÇÕES", "—", "Participação das três maiores"),
            "hhi": MetricCard("CONCENTRAÇÃO / HHI", "—", "0 a 1 • maior indica mais concentração"),
        }
        for metric in self.metrics.values():
            metrics.addWidget(metric, 1)
        self.content.addLayout(metrics)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.content.addWidget(self.feedback)
        self.table = DataTable(("ATIVO", "VALOR ATUAL BRL", "PESO"), [])
        chart_container = QWidget()
        self.chart_layout = QVBoxLayout(chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.visuals = ResponsivePair(chart_container, self.table, breakpoint=850, stretches=(5, 4))
        self.visuals.setProperty("surface", True)
        self.content.addWidget(self.visuals)
        self.chart: QChartView | None = None
        self.clear("Selecione uma carteira e aguarde valuation completo.")

    def clear(self, message: str) -> None:
        self.feedback.setText(message)
        for metric in self.metrics.values():
            metric.set_value("—")
        self.metrics["largest"].detail_label.setText("Participação no valor aberto")
        self.metrics["top_three"].detail_label.setText("Participação das três maiores")
        self.metrics["hhi"].setToolTip("HHI = soma dos pesos²; disponível com valuation BRL completo.")
        self.visuals.hide()
        replace_rows(self.table, [])
        if self.chart is not None:
            self.chart_layout.removeWidget(self.chart)
            self.chart.deleteLater()
            self.chart = None

    def display(self, valuation: PortfolioValuation) -> None:
        data = valuation.concentration
        self.clear(
            "Pesos sobre o valor aberto em BRL • HHI = soma dos pesos²; maior indica mais concentração."
            + (
                f" {data.reason} Ativos sem valuation BRL: {', '.join(data.unavailable_assets) or 'nenhum'}"
                if data.reason
                else ""
            )
        )
        replace_rows(
            self.table,
            [
                (
                    item.asset.symbol,
                    currency_text(item.market_value),
                    percent_text(item.weight),
                )
                for item in data.weights
            ],
        )
        if data.weights:
            self.metrics["largest"].set_value(percent_text(data.largest), "accent")
            self.metrics["largest"].detail_label.setText(data.weights[0].asset.symbol)
            self.metrics["top_three"].set_value(percent_text(data.top_three), "accent")
            self.metrics["top_three"].detail_label.setText(" + ".join(p.asset.symbol for p in data.weights[:3]))
            self.metrics["hhi"].set_value(f"{data.hhi:.3f}".replace(".", ",") if data.hhi is not None else "—")
            self.metrics["hhi"].setToolTip(f"HHI calculado: {decimal_text(data.hhi) if data.hhi is not None else '—'}")
            self.chart = allocation_donut([(p.asset.symbol, float(p.weight)) for p in data.weights])
            self.chart_layout.addWidget(self.chart)
            self.visuals.show()
