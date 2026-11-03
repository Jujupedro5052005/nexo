from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from nexo.application.portfolio.export_report import ExportReport
from nexo.application.portfolio.tax_worksheet import BuildTaxWorksheet
from nexo.calculations.projections.planning import allocate_contribution
from nexo.calculations.tax import manual_tax_scenario
from nexo.calculations.valuation.performance import EquityPoint, PortfolioPerformance
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.domain.models.transaction import Transaction


def test_manual_tax_scenario_compensation_withholding_and_loss_carry():
    result = manual_tax_scenario(
        Decimal(1000), Decimal(200), Decimal(".15"), Decimal(5)
    )
    assert (
        result.taxable_base,
        result.compensated_loss,
        result.remaining_loss,
        result.estimated_tax,
        result.payable,
    ) == (800, 200, 0, 120, 115)
    loss = manual_tax_scenario(Decimal(-300), Decimal(200), Decimal(".15"), Decimal(5))
    assert loss.remaining_loss == 500 and loss.payable == 0
    assert (
        manual_tax_scenario(
            Decimal(100), Decimal(200), Decimal(".15"), Decimal(50)
        ).payable
        == 0
    )


@pytest.mark.parametrize(
    "values",
    [
        ("NaN", "0", ".15", "0"),
        ("100", "-1", ".15", "0"),
        ("100", "0", "1.01", "0"),
        ("100", "0", ".15", "-1"),
        ("1e999999", "0", ".15", "0"),
        ("1e-999999", "0", ".15", "0"),
    ],
)
def test_tax_rejects_invalid_or_unbounded_assumptions(values):
    with pytest.raises(DomainValidationError):
        manual_tax_scenario(*(Decimal(x) for x in values))


def test_monthly_worksheet_uses_prior_year_costs_and_preserves_history():
    history = [
        Transaction(
            1,
            Asset("ITUB4"),
            TransactionType.BUY,
            Decimal(10),
            Decimal(10),
            Decimal(2),
            datetime(2025, 12, 1, tzinfo=timezone.utc),
        ),
        Transaction(
            1,
            Asset("ITUB4"),
            TransactionType.SELL,
            Decimal(4),
            Decimal(15),
            Decimal(1),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
        Transaction(
            1,
            Asset("ITUB4"),
            TransactionType.SELL,
            Decimal(2),
            Decimal(8),
            Decimal(1),
            datetime(2026, 2, 2, tzinfo=timezone.utc),
        ),
    ]
    case = BuildTaxWorksheet(SimpleNamespace(execute=lambda identity: history))
    rows = case.execute(1, 2026)
    assert len(rows) == 12 and len(history) == 3
    assert rows[0].sales == 60 and rows[0].realized == Decimal("18.2")
    assert rows[1].realized == Decimal("-5.4")
    assert rows[2].sales == 0 and rows[2].realized == 0
    assert rows[0].symbols == ("ITUB4",)


def test_tax_worksheet_replays_split_and_exports_exact_csv():
    history = [
        Transaction(
            1,
            Asset("ITUB4"),
            TransactionType.BUY,
            Decimal(10),
            Decimal(10),
            Decimal(0),
            datetime(2025, 12, 1, tzinfo=timezone.utc),
        ),
        Transaction(
            1,
            Asset("ITUB4"),
            TransactionType.SELL,
            Decimal(4),
            Decimal(8),
            Decimal(1),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
    ]
    split = PortfolioEvent(
        1,
        PortfolioEventType.SPLIT,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        asset=Asset("ITUB4"),
        ratio=Decimal(2),
    )
    listing = SimpleNamespace(execute=lambda identity: history)
    events = SimpleNamespace(list_events=lambda identity: (split,))
    assert BuildTaxWorksheet(listing, events).execute(1, 2026)[0].realized == 11
    written = []
    exporter = ExportReport(
        listing,
        None,
        None,
        SimpleNamespace(write=lambda path, text: written.append((path, text))),
        events,
    )
    assert exporter.execute("tax", 1, "worksheet.csv", year=2026) == 12
    assert "resultado_contabil_brl" in written[0][1]
    assert "1;2026;1;32;1;11;ITUB4" in written[0][1]


def test_twr_flow_summary_distinguishes_unknown_from_zero():
    assert PortfolioPerformance((), None, ()).total_external_flow is None
    day = datetime(2026, 1, 1, tzinfo=timezone.utc).date()
    points = (
        EquityPoint(day, Decimal(100), Decimal(0), Decimal(100), Decimal(100), None),
        EquityPoint(day, Decimal(80), Decimal(0), Decimal(80), Decimal(-20), None),
    )
    assert PortfolioPerformance(points, None, ()).total_external_flow == 80


def test_planning_allocation_conserves_contribution_and_rejects_invalid_sum():
    assert allocate_contribution(
        Decimal(1500), (Decimal(".3"), Decimal(".5"), Decimal(".2"))
    ) == (450, 750, 300)
    with pytest.raises(DomainValidationError, match="100%"):
        allocate_contribution(Decimal(1500), (Decimal(".2"), Decimal(".5")))
