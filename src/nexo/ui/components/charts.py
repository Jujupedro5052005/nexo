from collections.abc import Sequence
from math import fsum

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QDateTime, QMargins, QPointF, Qt, QTimeZone
from PySide6.QtGui import QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QToolTip

from nexo.domain.models.market_data import PriceHistory
from nexo.ui.styles.theme import BORDER, TEXT_PRIMARY, TEXT_SECONDARY


def _view(chart: QChart, minimum_height: int = 220) -> QChartView:
    chart.setBackgroundVisible(False)
    chart.legend().setLabelColor(QColor(TEXT_SECONDARY))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    view = QChartView(chart)
    view.setBackgroundBrush(QColor("#0C1727"))
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setStyleSheet("background: transparent; border: 0;")
    view.setMinimumHeight(minimum_height)
    return view


def line_chart(
    series_data: Sequence[tuple[str, Sequence[float], str]],
    minimum_height: int = 240,
) -> QChartView:
    chart = QChart()
    axis_x = QValueAxis()
    axis_y = QValueAxis()
    longest = max((len(values) for _, values, _ in series_data), default=1)
    all_values = [value for _, values, _ in series_data for value in values]
    axis_x.setRange(0, max(1, longest - 1))
    axis_x.setLabelFormat("%d")
    axis_x.setTitleText("Período")
    low, high = min(all_values, default=0), max(all_values, default=1)
    margin = max(1, (high - low) * 0.15)
    axis_y.setRange(low - margin, high + margin)
    axis_y.setLabelFormat("%.0f")
    for axis in (axis_x, axis_y):
        axis.setLabelsColor(QColor(TEXT_SECONDARY))
        axis.setTitleBrush(QColor(TEXT_SECONDARY))
        axis.setGridLineColor(QColor(BORDER))
        axis.setLinePenColor(QColor(BORDER))
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    for name, values, color in series_data:
        series = QLineSeries()
        series.setName(name)
        series.setPen(QPen(QColor(color), 2.2))
        for index, value in enumerate(values):
            series.append(QPointF(index, value))
        chart.addSeries(series)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        series.hovered.connect(
            lambda point, state, label=name: (
                QToolTip.showText(QCursor.pos(), f"{label}: {point.y():.2f}")
                if state
                else QToolTip.hideText()
            )
        )
    return _view(chart, minimum_height)


def donut_chart(items: Sequence[tuple[str, int, str, str]]) -> QChartView:
    series = QPieSeries()
    series.setHoleSize(0.58)
    for label, percent, _value, color in items:
        pie_slice = series.append(label, percent)
        pie_slice.setBrush(QColor(color))
        pie_slice.setPen(QPen(QColor("#0C1727"), 2))
        pie_slice.setLabel(f"{label}: {percent}%")
        pie_slice.hovered.connect(
            lambda state, target=pie_slice: target.setExploded(state)
        )
    chart = QChart()
    chart.addSeries(series)
    chart.legend().setVisible(False)
    return _view(chart, 220)


def allocation_donut(items: Sequence[tuple[str, float]]) -> QChartView:
    """Draw existing weights; grouping is visual only and preserves their sum.

    Float conversion belongs solely to Qt coordinates. The full asset table is
    retained by the caller; no weights or financial metrics are recalculated.
    """
    ordered = sorted(items, key=lambda item: (-item[1], item[0]))
    display = [(label, weight, label) for label, weight in ordered]
    if len(ordered) > 8:
        display = display[:6] + [
            ("Outros", fsum(weight for _, weight in ordered[6:]),
             ", ".join(label for label, _ in ordered[6:]))
        ]
    colors = ("#10C7C7", "#4D7CFF", "#7193CF", "#8B82BC", "#4D9C9C", "#7793AA", "#53667E", "#A2B3C8")
    series = QPieSeries()
    series.setHoleSize(0.60)
    series.setPieSize(0.82)
    for index, (name, weight, members) in enumerate(display):
        percentage = f"{weight * 100:.1f}%".replace(".", ",")
        pie_slice = series.append(percentage, weight)
        pie_slice.setBrush(QColor(colors[index]))
        pie_slice.setPen(QPen(QColor("#0C1727"), 2))
        pie_slice.setLabelBrush(QColor(TEXT_PRIMARY))
        pie_slice.setLabelPosition(pie_slice.LabelPosition.LabelInsideHorizontal)
        pie_slice.setLabelVisible(weight >= 0.08)
        pie_slice.hovered.connect(
            lambda state, text=f"{name}: {percentage}\n{members}": (
                QToolTip.showText(QCursor.pos(), text) if state else QToolTip.hideText()
            )
        )
    chart = QChart()
    chart.setMargins(QMargins(4, 4, 4, 4))
    chart.addSeries(series)
    view = _view(chart, 320)
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
    for marker, (name, weight, _) in zip(chart.legend().markers(series), display, strict=True):
        marker.setLabel(f"{name} · {weight * 100:.1f}%".replace(".", ","))
    return view


def bar_chart(
    categories: Sequence[str],
    groups: Sequence[tuple[str, Sequence[float], str]],
    minimum_height: int = 220,
) -> QChartView:
    series = QBarSeries()
    for name, values, color in groups:
        bar_set = QBarSet(name)
        bar_set.append(list(values))
        bar_set.setColor(QColor(color))
        bar_set.setBorderColor(QColor(color))
        series.append(bar_set)
    chart = QChart()
    chart.addSeries(series)
    axis_x = QBarCategoryAxis()
    axis_x.append(list(categories))
    axis_x.setLabelsColor(QColor(TEXT_SECONDARY))
    axis_y = QValueAxis()
    axis_y.setLabelsColor(QColor(TEXT_SECONDARY))
    axis_y.setGridLineColor(QColor(BORDER))
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_x)
    series.attachAxis(axis_y)
    return _view(chart, minimum_height)


def historical_chart(history: PriceHistory) -> QChartView:
    """Decimal becomes float only at Qt's drawing boundary, never in valuation."""
    chart = QChart()
    series = QLineSeries()
    series.setName(f"{history.asset.symbol} • fechamento informado pela API")
    for point in history.points:
        series.append(point.timestamp.timestamp() * 1000, float(point.close))
    chart.addSeries(series)
    dates = QDateTimeAxis()
    dates.setFormat("dd/MM/yy")
    dates.setTickCount(max(2, min(5, len(history.points))))
    dates.setTitleText("Data (UTC)")
    prices = QValueAxis()
    prices.setLabelFormat("%.2f")
    for axis in (dates, prices):
        axis.setLabelsColor(QColor(TEXT_SECONDARY))
        axis.setGridLineColor(QColor(BORDER))
    chart.addAxis(dates, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(prices, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(dates)
    series.attachAxis(prices)
    if history.points:
        first = int(history.points[0].timestamp.timestamp() * 1000)
        last = int(history.points[-1].timestamp.timestamp() * 1000)
        dates.setRange(
            QDateTime.fromMSecsSinceEpoch(first, QTimeZone.utc()),
            QDateTime.fromMSecsSinceEpoch(max(first + 86400000, last), QTimeZone.utc()),
        )
        values = [float(point.close) for point in history.points]
        margin = max(0.01, (max(values) - min(values)) * 0.1)
        prices.setRange(min(values) - margin, max(values) + margin)
    return _view(chart, 240)
