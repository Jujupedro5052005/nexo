from collections.abc import Sequence

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QToolTip

from nexo.ui.styles.theme import BORDER, TEXT_SECONDARY


def _view(chart: QChart, minimum_height: int = 220) -> QChartView:
    chart.setBackgroundVisible(False)
    chart.legend().setLabelColor(QColor(TEXT_SECONDARY))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    view = QChartView(chart)
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
            lambda point, state, label=name: QToolTip.showText(
                QCursor.pos(), f"{label}: {point.y():.2f}"
            )
            if state
            else QToolTip.hideText()
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
