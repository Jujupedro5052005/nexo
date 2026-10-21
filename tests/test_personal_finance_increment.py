from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from nexo.application.financial_planning.manage_finances import ManageFinances
from nexo.application.portfolio.dashboard import ledger_timeline
from nexo.application.portfolio.export_report import ExportReport
from nexo.calculations.projections.planning import goal_projection, monthly_budget
from nexo.calculations.valuation.decision import decision_scenario
from nexo.calculations.valuation.trade import preview_trade
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.market_data_provider import QuoteBatch
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal, PriceAlert
from nexo.domain.models.position import Position
from nexo.domain.models.transaction import Transaction
from nexo.infrastructure.database.repositories.personal_finance import (
    SqlPersonalFinanceRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)

D = Decimal
TODAY = date(2026, 10, 21)


@pytest.fixture
def repository(tmp_path):
    engine = create_database_engine(tmp_path / "finance.db")
    initialize_database(engine)
    yield SqlPersonalFinanceRepository(create_session_factory(engine))
    engine.dispose()


def test_planning_roundtrip_update_and_month_filter(repository):
    repository.save_budget(BudgetEntry("Salário", D("5000.001"), "income", TODAY))
    repository.save_budget(BudgetEntry("Aluguel", D(1000), "fixed", TODAY))
    repository.save_budget(
        BudgetEntry("Outra data", D(999), "income", date(2026, 9, 1))
    )
    entry = repository.budget_entries()[0]
    repository.save_budget(replace(entry, amount=D("6000.001")))
    summary = monthly_budget(repository.budget_entries(), TODAY)
    assert summary.income == D("6000.001") and summary.available == D("5000.001")
    assert len(repository.budget_entries()) == 3


def test_goal_roundtrip_and_projection(repository):
    repository.save_goal(FinancialGoal("Reserva", D(10000), D(2000), date(2027, 2, 21)))
    goal = repository.goals()[0]
    assert goal_projection(goal, TODAY) == (D(".2"), D(2000))
    assert goal_projection(replace(goal, deadline=date(2026, 1, 1)), TODAY) == (
        D(".2"),
        None,
    )
    assert goal_projection(replace(goal, current=D(11000)), TODAY) == (D(1), D(0))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: BudgetEntry("", D(1), "income", TODAY),
        lambda: BudgetEntry("X", D(-1), "fixed", TODAY),
        lambda: FinancialGoal("X", D(0), D(1), TODAY),
        lambda: PriceAlert("PETR4", D("NaN"), "below"),
    ],
)
def test_finance_models_reject_invalid_values(factory):
    with pytest.raises(DomainValidationError):
        factory()


def test_alerts_persist_snapshot_and_do_not_trigger_on_missing_or_foreign_quotes(
    repository,
):
    for symbol in ("ITSA4", "PETR4", "VALE3"):
        repository.save_alert(PriceAlert(symbol, D(20), "below"))
    from contextlib import nullcontext

    market = SimpleNamespace(
        refresh_context=lambda _: nullcontext(),
        get_quotes=lambda assets: QuoteBatch(
            (
                Quote(
                    Asset("ITSA4"),
                    D(19),
                    "BRL",
                    "Itaúsa",
                    datetime.now(timezone.utc),
                    source="fixture",
                ),
                Quote(Asset("VALE3"), D(10), "USD", "Vale", datetime.now(timezone.utc)),
            )
        ),
    )
    ManageFinances(repository, market).check_alerts()
    a, b, c = repository.alerts()
    assert (
        a.triggered_at
        and a.state == "Condição atingida na cotação"
        and "fixture" in a.quote_at
    )
    assert not b.triggered_at and not c.triggered_at
    assert b.state == c.state == "Cotação BRL indisponível"
    trigger = a.triggered_at
    ManageFinances(repository, market).check_alerts()
    assert repository.alerts()[0].triggered_at == trigger


def test_decision_scenario_uses_lower_ceiling_and_no_fabricated_trend():
    result = decision_scenario(D(70), (D(100), D(90)), D(6), None)
    assert result.ceiling == 90 and result.entry == 72 and result.review == 90
    assert result.dividend_yield.quantize(D(".000001")) == D(".085714")
    assert "compra" in result.reading and "insuficiente" in result.trend
    assert decision_scenario(None, (None,), None, None).upside is None
    with pytest.raises(ValueError):
        decision_scenario(D(70), (D(90),), None, None, D(1))


def transaction(
    kind=TransactionType.BUY, quantity="10", price="20", fees="2", month=10
):
    return Transaction(
        1,
        Asset("ITSA4"),
        kind,
        D(quantity),
        D(price),
        D(fees),
        datetime(2026, month, 1, tzinfo=timezone.utc),
    )


def test_trade_preview_and_ledger_timeline_preserve_fees_and_partial_sale():
    purchase = transaction()
    sale = transaction(TransactionType.SELL, quantity="5", price="25", month=11)
    points = ledger_timeline([purchase, sale])
    assert points[0].cost == 202 and points[1].cost == 101
    assert points[1].realized == 22
    position = Position(1, Asset("ITSA4"), D(10), D("20.2"), D(202), D(0))
    preview = preview_trade(sale, position)
    assert preview.remaining == 5 and preview.realized == 22
    assert preview_trade(purchase, None).average_cost == D("20.2")


def test_reports_use_real_rows_and_neutralize_spreadsheet_formula(repository):
    repository.save_goal(FinancialGoal("=HYPERLINK(1)", D(1000), D(20), TODAY))
    contents = []
    case = ExportReport(
        None,
        None,
        ManageFinances(repository, None),
        SimpleNamespace(write=lambda path, text: contents.append(text)),
    )
    assert case.execute("goals", None, "unused.csv") == 1
    assert "'=HYPERLINK(1)" in contents[0] and "1000" in contents[0]
    with pytest.raises(ValueError):
        case.execute("transactions", None, "unused.csv")


def test_real_finance_forms_save_edit_and_reload(qtbot, repository):
    from nexo.ui.pages.personal_finance import GoalsPage, PlanningPage

    service = ManageFinances(repository, None)
    page = PlanningPage(service)
    qtbot.addWidget(page)
    page.edit()
    editor = page.editor
    fields = editor.findChildren(
        __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit
    )
    fields[0].setText("Salário")
    fields[1].setText("5000,50")
    from PySide6.QtWidgets import QDialogButtonBox

    editor.findChild(QDialogButtonBox).button(
        QDialogButtonBox.StandardButton.Save
    ).click()
    assert repository.budget_entries()[0].amount == D("5000.50")
    assert page.table.rowCount() == 1
    goals = GoalsPage(service)
    qtbot.addWidget(goals)
    repository.save_goal(FinancialGoal("Reserva", D(1000), D(100), TODAY))
    goals.reload()
    assert goals.table.rowCount() == 1 and "10" in goals.table.item(0, 4).text()
