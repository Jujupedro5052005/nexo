import gc
from datetime import datetime, timezone
from decimal import Decimal

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget
from shiboken6 import isValid

from nexo.ui.components.charts import (
    allocation_donut,
    capital_timeline_chart,
    line_chart,
)


def test_repeated_chart_replacement_retains_boundaries_until_widget_disposal(
    qapp, qtbot
):
    host = QWidget()
    qtbot.addWidget(host)
    layout = QVBoxLayout(host)
    previous = None
    for i in range(45):
        if previous is not None:
            layout.removeWidget(previous)
            previous.deleteLater()
        view = capital_timeline_chart(
            [
                (datetime(2026, 1, 1, tzinfo=timezone.utc), Decimal(100 + i)),
                (datetime(2026, 2, 1, tzinfo=timezone.utc), Decimal(200 + i)),
            ]
        )
        layout.addWidget(view)
        gc.collect()
        area = view.chart().series()[0]
        assert isValid(area.upperSeries())
        assert area.upperSeries().parent() is area
        assert area.upperSeries().count() == 2
        temporary = (
            allocation_donut([("A", 0.4), ("B", 0.6)])
            if i % 2
            else line_chart([("A", [1.0, 2.0, 3.0], "#10C7C7")])
        )
        temporary.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        previous = view
