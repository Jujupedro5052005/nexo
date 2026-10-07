from datetime import datetime, timezone
from decimal import Decimal
from math import fsum

import pytest
from PySide6.QtCharts import QPieSeries
from PySide6.QtWidgets import QBoxLayout

from nexo.calculations.valuation.portfolio import value_portfolio
from nexo.domain.interfaces.market_data_provider import QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.domain.models.position import Position
from nexo.domain.reconstruction import ReconstructionResult
from nexo.ui.components.concentration_panel import ConcentrationPanel
from nexo.ui.pages.overview_page import OverviewPage


def valuation(count=3, *, missing=False, price_scale=Decimal(1)):
    positions = tuple(Position(1, Asset(f"TEST{i}"), Decimal(10), Decimal(3),
                               Decimal(30), Decimal(0)) for i in range(count))
    quotes = tuple(Quote(p.asset, Decimal(i+1) * price_scale, "BRL", p.asset.symbol,
                         datetime(2026, 10, 7, tzinfo=timezone.utc), source="test fixture")
                   for i, p in enumerate(positions) if not missing or i)
    return value_portfolio(ReconstructionResult(positions, ()), QuoteBatch(quotes))


@pytest.mark.parametrize("count", [1, 3, 8, 12])
def test_donut_uses_existing_weights_and_keeps_full_table(qtbot, count):
    panel = ConcentrationPanel()
    qtbot.addWidget(panel)
    value = valuation(count)
    before = value.concentration
    panel.display(value)
    series = panel.chart.chart().series()[0]
    assert isinstance(series, QPieSeries)
    assert series.holeSize() == pytest.approx(0.60)
    slices = series.slices()
    weights = [float(p.weight) for p in before.weights]
    expected = weights if count <= 8 else weights[:6] + [fsum(weights[6:])]
    assert [s.value() for s in slices] == pytest.approx(expected)
    assert fsum(s.value() for s in slices) == pytest.approx(fsum(weights))
    assert panel.table.rowCount() == count
    assert value.concentration == before
    markers = panel.chart.chart().legend().markers(series)
    if count > 8:
        assert markers[-1].label().startswith("Outros")
    assert all("%" in marker.label() for marker in markers)
    assert panel.metrics["top_three"].detail_label.text() == " + ".join(
        p.asset.symbol for p in before.weights[:3])


@pytest.mark.parametrize("count, missing", [(0, False), (3, True)])
def test_incomplete_or_empty_portfolio_never_draws_misleading_donut(qtbot, count, missing):
    panel = ConcentrationPanel()
    qtbot.addWidget(panel)
    panel.display(valuation())
    assert panel.chart is not None
    panel.display(valuation(count, missing=missing))
    assert panel.chart is None
    assert panel.table.rowCount() == 0
    assert panel.metrics["top_three"].value_label.text() == "—"
    assert panel.metrics["hhi"].value_label.text() == "—"


def test_overview_cards_align_and_stack_at_narrow_width(qtbot):
    page = OverviewPage()
    qtbot.addWidget(page)
    page.resize(1450, 900)
    page.show()
    qtbot.waitUntil(lambda: page.demo_charts.row.direction() == QBoxLayout.Direction.LeftToRight)
    left, right = page.evolution_card, page.insights_card
    assert left.y() == right.y()
    assert left.width() > right.width()
    assert left.height() == right.height()
    assert right.x() >= left.x() + left.width() + 14
    page.resize(930, 900)
    qtbot.waitUntil(lambda: page.demo_charts.row.direction() == QBoxLayout.Direction.TopToBottom)
    assert left.x() == right.x()
    assert right.y() >= left.y() + left.height() + 14
    page.resize(1450, 900)
    qtbot.waitUntil(lambda: page.demo_charts.row.direction() == QBoxLayout.Direction.LeftToRight)
    assert left.y() == right.y()


def test_metric_states_reset_after_market_failure_and_context_change(qtbot):
    page = OverviewPage()
    qtbot.addWidget(page)
    page.set_market_data(valuation(price_scale=Decimal(4)))
    assert page.metrics["market"].value_label.property("metricState") == "accent"
    assert page.metrics["unrealized"].value_label.property("metricState") == "positive"
    page.set_market_data(valuation())
    assert page.metrics["unrealized"].value_label.property("metricState") == "negative"
    assert page.metrics["return"].value_label.property("metricState") == "negative"
    page.clear_market_data("Offline")
    assert page.metrics["unrealized"].value_label.text() == "—"
    assert page.metrics["unrealized"].value_label.property("metricState") == "neutral"
    assert page.concentration_panel.chart is None
    assert "HHI calculado:" not in page.concentration_panel.metrics["hhi"].toolTip()
