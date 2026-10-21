from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from threading import Barrier, Event

import pytest

from nexo.application.analysis.research_tools import TOOLS, EvaluateResearchTool
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.calculations.indicators.insolvency import insolvency_scores
from nexo.calculations.indicators.technical import technical_indicators
from nexo.calculations.projections.finance import (
    amortization,
    bond_metrics,
    discounted_company,
    future_value,
    irr,
    npv,
    real_rate,
    required_payment,
)
from nexo.calculations.risk.market import comparative_risk, tail_risk
from nexo.calculations.valuation.performance import portfolio_performance
from nexo.core.cancellation import OperationCancelled, current_cancellation
from nexo.domain.enums.transaction_type import TransactionType as TT
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.models.portfolio_event import PortfolioEvent as E
from nexo.domain.models.portfolio_event import PortfolioEventType as K
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions
from nexo.domain.services.cash_ledger import InsufficientCashError, cash_state
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from nexo.infrastructure.market_data.yahoo_transport import yahoo_request

START = datetime(2026, 1, 1, 9)  # noqa: DTZ001 -- same wall-clock convention as transaction forms
A = Asset("PETR4")


def trade(day=0, kind=TT.BUY, qty="10", price="10", fees="0"):
    return Transaction(
        1, A, kind, D(qty), D(price), D(fees), START + timedelta(days=day, hours=1)
    )


def event(kind=K.OPENING, amount="1000", day=0, **kwargs):
    return E(1, kind, START + timedelta(days=day), D(amount), **kwargs)


def history(prices, **kwargs):
    return PriceHistory(
        A,
        tuple(
            HistoricalPrice(
                (START + timedelta(days=i)).replace(tzinfo=timezone.utc), D(p)
            )
            for i, p in enumerate(prices)
        ),
        "max",
        START.replace(tzinfo=timezone.utc),
        "fixture",
        **kwargs,
    )


def test_cash_is_unknown_until_explicit_opening_and_no_implicit_deposits():
    assert cash_state([trade()], ()).balance is None
    with pytest.raises(DomainValidationError):
        cash_state([], (event(K.DEPOSIT),))
    assert cash_state([trade()], (event(day=1, amount="50"),)).balance == 50
    with pytest.raises(InsufficientCashError):
        cash_state([trade(fees="1")], (event(amount="100"),))


def test_receipts_retention_and_costs_are_internal():
    events = (
        event(),
        event(K.DEPOSIT, "20", day=1),
        event(K.JCP, "10", day=2, asset=A, withholding=D("1.5")),
        event(K.FEE, "3", day=2),
        event(K.TAX, "2", day=2),
        event(K.WITHDRAWAL, "30", day=3),
    )
    state = cash_state([trade(fees="1")], events)
    assert state.balance == D("892.5")
    assert state.income == D("8.5")
    assert state.costs == D("7.5")
    assert sum(e.external_flow for e in events) == -10
    with pytest.raises(DomainValidationError):
        cash_state([], (event(), event(day=2)))
    with pytest.raises(DomainValidationError):
        event(currency="USD")
    with pytest.raises(DomainValidationError):
        cash_state(
            [],
            (
                event(),
                replace(
                    event(K.DEPOSIT), occurred_at=START.replace(tzinfo=timezone.utc)
                ),
            ),
        )


def test_split_preserves_basis_and_realized_result_and_allows_postsplit_sale():
    split = event(K.SPLIT, "0", day=1, asset=A, ratio=D(2))
    result = rebuild_positions(
        [trade(), trade(day=2, kind=TT.SELL, qty="5", price="6")], (split,)
    )
    p = result.positions[0]
    assert (p.quantity, p.average_cost, p.cost_basis, p.realized_profit_loss) == (
        D(15),
        D(5),
        D(75),
        D(5),
    )


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "atomic.db"
    engine = create_database_engine(path)
    initialize_database(engine)
    factory = create_session_factory(engine)
    SqlAlchemyPortfolioRepository(factory).add(Portfolio("Teste"))
    repo = SqlAlchemyTransactionRepository(factory)
    yield path, repo
    engine.dispose()


@pytest.mark.parametrize("spending", [False, True])
def test_two_independent_writers_cannot_oversell_or_double_spend(ledger, spending):
    path, repo = ledger
    if spending:
        repo.add_event(event(amount="150"))
        candidate = trade()
        expected = InsufficientCashError
    else:
        RegisterTransaction(repo).execute(trade())
        candidate = trade(day=1, kind=TT.SELL)
        expected = InsufficientPositionError
    barrier = Barrier(2)

    def write():
        engine = create_database_engine(path)
        other = SqlAlchemyTransactionRepository(create_session_factory(engine))
        try:
            barrier.wait(timeout=5)
            try:
                return RegisterTransaction(other).execute(candidate)
            except expected:
                return None
        finally:
            engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: write(), range(2)))
    assert sum(r is not None for r in results) == 1
    assert len(repo.list_by_portfolio(1)) == (1 if spending else 2)


def test_event_replays_later_operations_and_rolls_back(ledger):
    _, repo = ledger
    repo.add_event(event(amount="110"))
    RegisterTransaction(repo).execute(trade(day=2, fees="1"))
    with pytest.raises(InsufficientCashError):
        repo.add_event(event(K.WITHDRAWAL, "20", day=1))
    assert len(repo.list_events(1)) == 1
    assert cash_state(repo.list_by_portfolio(1), repo.list_events(1)).balance == 9


def test_external_flows_do_not_become_twr_profit_and_income_is_internal():
    events = (
        event(amount="100"),
        event(K.DEPOSIT, "100", day=1),
        event(K.WITHDRAWAL, "50", day=2),
    )
    result = portfolio_performance([], events, {}, (START + timedelta(days=2)).date())
    assert result.twr == 0 and result.points[-1].equity == 150
    result = portfolio_performance(
        [],
        (*events, event(K.DIVIDEND, "10", day=2, asset=A)),
        {},
        (START + timedelta(days=2)).date(),
    )
    assert result.twr == D(".05")


def test_twr_price_gain_missing_coverage_and_legacy_cash():
    result = portfolio_performance(
        [trade()],
        (event(amount="100"),),
        {A: history(["10", "11"])},
        (START + timedelta(days=1)).date(),
    )
    assert result.twr == D(".1")
    missing = portfolio_performance(
        [trade()], (event(amount="100"),), {}, (START + timedelta(days=1)).date()
    )
    assert missing.twr is None and missing.issues
    assert portfolio_performance([trade()], (), {}, START.date()).twr is None


def test_split_adjusted_history_requires_matching_event():
    at = (START + timedelta(days=1)).replace(tzinfo=timezone.utc)
    h = history(["5", "5"], splits=((at, D(2)),), split_adjusted=True)
    opening = event(amount="100")
    result = portfolio_performance(
        [trade()], (opening,), {A: h}, (START + timedelta(days=1)).date()
    )
    assert result.twr is None and any("split" in i for i in result.issues)
    split = event(K.SPLIT, "0", day=1, asset=A, ratio=D(2))
    result = portfolio_performance(
        [trade()], (opening, split), {A: h}, (START + timedelta(days=1)).date()
    )
    assert result.twr == 0
    assert [p.equity for p in result.points] == [D(100), D(100)]


def test_var_reference_quantile_and_es_with_real_tail():
    returns = tuple(-D(i) / 1000 for i in range(1, 101))
    risk = tail_risk(returns, D(1000), D(".95"))
    assert risk.historical_var == 95
    assert risk.historical_es == D("97.5")
    assert risk.normal_es >= risk.normal_var
    assert tail_risk((D(0),) * 30, D(100)).historical_var == 0
    with pytest.raises(DomainValidationError):
        tail_risk(returns[:10], D(100))
    with pytest.raises(DomainValidationError):
        tail_risk(returns, D(-1))


def test_comparative_statistics_and_constant_series():
    x = (D("-.02"), D(".01"), D(".03"), D("-.01"))
    b = tuple(v / 2 for v in x)
    result = comparative_risk(x, b, D(0))
    assert abs(result["beta"] - 2) < D("1e-45")
    assert abs(result["correlation"] - 1) < D("1e-45")
    assert comparative_risk((D(0),) * 4, (D(0),) * 4, D(0))["sharpe"] is None


def test_flat_and_rising_technical_series():
    flat = technical_indicators(history(["10"] * 210))
    assert flat["IFR14"] == 50 and flat["MACD 12/26"] == 0
    assert flat["MM200"] == flat["Bollinger inferior"] == 10
    up = technical_indicators(history([str(i) for i in range(1, 211)]))
    assert up["IFR14"] == 100 and up["MM20"] == D("200.5")
    assert technical_indicators(history(["10"]))["MM20"] is None


def test_financial_projection_reference_values_and_invalid_irr():
    assert future_value(D(100), D(10), D(0), 12) == 220
    assert required_payment(D(220), D(100), D(0), 12) == 10
    assert abs(real_rate(D(".1"), D(".05")) - D(1) / 21) < D("1e-26")
    assert npv((D(-100), D(110)), D(".1")) == 0
    assert abs(irr((D(-100), D(110))) - D(".1")) < D("1e-20")
    with pytest.raises(DomainValidationError):
        irr((D(-100), D(230), D(-132)))
    with pytest.raises(DomainValidationError):
        future_value(D("NaN"), D(0), D(0), 2)
    for system in ("PRICE", "SAC"):
        rows = amortization(D(1000), D(".01"), 12, system)
        assert rows[-1].balance == 0
        assert abs(sum(r.principal for r in rows) - 1000) <= D("1e-24")
    bond = bond_metrics(D(100), D(10), D(".1"), 1)
    assert bond[:2] == (D(100), D(1))
    assert abs(bond[2] - D(1) / D("1.1")) < D("1e-27")
    assert discounted_company((D(10),), D(".1"), D(0), D(0), D(1)) == 100


def test_insolvency_coefficients_aligned_accounts_and_missing_inputs():
    keys = {
        k
        for pairs in __import__(
            "nexo.calculations.indicators.insolvency", fromlist=["MODELS"]
        ).MODELS.values()
        for pair in pairs
        for k in pair
    }
    values = dict.fromkeys(keys, D(100))
    # All ratios equal one, except derived sums below: long liquidity=2; quick=0.
    values.update(current_assets=D(100), long_receivables=D(100), inventory=D(100))
    scores = insolvency_scores(values, nonfinancial=True, aligned=True)
    assert scores[0].score == D("2.96")
    assert scores[1].score == D("1.96")
    assert scores[2].score == D("14.277")
    assert all(
        s.score is None for s in insolvency_scores({}, nonfinancial=True, aligned=True)
    )
    with pytest.raises(DomainValidationError):
        insolvency_scores(values, nonfinancial=False, aligned=True)


def test_all_registry_tools_have_executable_metadata():
    assert len(TOOLS) >= 20
    assert len({t.key for t in TOOLS}) == len(TOOLS)
    assert all(t.fields and t.reference and t.description for t in TOOLS)
    result = EvaluateResearchTool().execute(
        "compound",
        {"capital": D(100), "payment": D(10), "rate": D(0), "periods": D(12)},
    )
    assert result.rows and any(r[1] == 220 for r in result.rows)


def test_cancelled_yahoo_transport_never_starts_a_request():
    token = Event()
    token.set()
    context = current_cancellation.set(token)
    try:
        with pytest.raises(OperationCancelled):
            yahoo_request("PETR4.SA", "get_info")
    finally:
        current_cancellation.reset(context)


@pytest.mark.parametrize("spec", TOOLS, ids=lambda s: s.key)
def test_each_tool_executes_valid_manual_scenario(spec):
    values = {}
    for f in spec.fields:
        values[f.key] = (
            (D(-100), D(60), D(60))
            if f.key == "flows" and spec.key == "project"
            else (D(10), D(11))
            if f.kind == "series"
            else (D("-.2"), D(".1"))
            if f.kind == "percent_series"
            else D(".1")
            if f.kind == "percent"
            else D(12)
            if f.kind == "int"
            else D(100)
        )
    values.update(
        {
            k: v
            for k, v in {
                "growth": D(".02"),
                "participation": D(".1"),
                "liabilities": D(20),
                "expenses": D(50),
                "installments": D(10),
            }.items()
            if k in values
        }
    )
    result = EvaluateResearchTool().execute(spec.key, values)
    assert result.rows and all(r[3] for r in result.rows)


def test_account_form_reopens_persisted_cash_and_real_trade(qtbot, ledger):
    from nexo.application.portfolio.account import PortfolioAccount
    from nexo.ui.components.account_panel import AccountPanel

    _, repo = ledger
    panel = AccountPanel(PortfolioAccount(repo, repo, None))
    qtbot.addWidget(panel)
    panel.set_portfolio(1)
    panel.amount.setText("200")
    panel.when.setDateTime(
        __import__("PySide6.QtCore", fromlist=["QDateTime"]).QDateTime.fromString(
            "2026-01-01T09:00:00", "yyyy-MM-ddTHH:mm:ss"
        )
    )
    panel.register()
    assert panel.table.rowCount() == 1
    RegisterTransaction(repo).execute(trade())
    panel.set_portfolio(1)
    assert cash_state(repo.list_by_portfolio(1), repo.list_events(1)).balance == 100
    assert "100,00" in panel.feedback.text()


def test_calculator_ui_invalidates_previous_scenario_and_explains_numbers(qtbot):
    from nexo.ui.components.research_workbench import CalculatorPanel

    panel = CalculatorPanel()
    qtbot.addWidget(panel)
    for key, value in {
        "capital": "100",
        "payment": "10",
        "rate": "0",
        "periods": "12",
    }.items():
        panel.inputs[key].setText(value)
    panel.run()
    assert "220,00" in panel.table.item(0, 1).text()
    assert panel.table.item(0, 0).toolTip()
    panel.inputs["capital"].setText("200")
    assert panel.table.rowCount() == 0


def test_worker_cancel_suppresses_delivery_and_stops_operation(qtbot):
    import time

    from nexo.core.cancellation import check_cancelled
    from nexo.ui.workers import TaskRunner

    runner = TaskRunner()
    began = Event()
    ended = Event()
    delivered = []

    def work():
        began.set()
        try:
            while True:
                check_cancelled()
                time.sleep(0.005)
        finally:
            ended.set()

    runner.submit(work, lambda *args: delivered.append(args))
    qtbot.waitUntil(began.is_set)
    runner.cancel()
    qtbot.waitUntil(ended.is_set)
    runner.wait()
    qtbot.wait(20)
    assert not delivered
    runner.stop()


def test_owned_yahoo_process_is_terminated_after_cancel(monkeypatch):
    from nexo.infrastructure.market_data import yahoo_transport as transport

    token = Event()
    actions = []

    class Connection:
        def close(self):
            pass

        def poll(self, _timeout):
            token.set()
            return False

    class Process:
        pid = 123

        def start(self):
            actions.append("start")

        def is_alive(self):
            return True

        def terminate(self):
            actions.append("terminate")

        def join(self, timeout):
            actions.append("join")

        def close(self):
            actions.append("close")

    class Context:
        def Pipe(self, **kwargs):
            return Connection(), Connection()

        def Process(self, **kwargs):
            return Process()

    monkeypatch.setattr(transport, "get_context", lambda _: Context())
    context = current_cancellation.set(token)
    try:
        with pytest.raises(OperationCancelled):
            transport.yahoo_request("PETR4.SA", "get_info")
    finally:
        current_cancellation.reset(context)
    assert actions == ["start", "terminate", "join", "close"]


def test_cash_and_performance_ignore_host_decimal_precision():
    from decimal import localcontext

    with localcontext() as context:
        context.prec = 6
        amount = "123456789.123456789"
        state = cash_state(
            [],
            (
                event(amount=amount),
                event(
                    K.DIVIDEND,
                    ".123456789",
                    day=1,
                    asset=A,
                    withholding=D(".000000001"),
                ),
            ),
        )
        assert state.balance == D("123456789.246913577")
        result = portfolio_performance(
            [],
            (event(amount="100"), event(K.DEPOSIT, "100", day=1)),
            {},
            (START + timedelta(days=1)).date(),
        )
        assert result.twr == 0


def test_duplicate_split_is_not_applied_twice(ledger):
    _, repo = ledger
    RegisterTransaction(repo).execute(trade())
    split = event(K.SPLIT, "0", day=1, asset=A, ratio=D(2))
    repo.add_event(split)
    with pytest.raises(DomainValidationError):
        repo.add_event(split)
    assert len(repo.list_events(1)) == 1


def test_events_export_exact_values_and_escape_user_notes(ledger):
    from nexo.application.portfolio.export_report import ExportReport
    from nexo.application.portfolio.list_transactions import ListTransactions
    from nexo.application.portfolio.load_portfolio_positions import (
        LoadPortfolioPositions,
    )

    _, repo = ledger
    repo.add_event(event(amount="100.00000001", note="=danger"))

    class Writer:
        content = ""

        def write(self, path, content):
            self.content = content

    writer = Writer()
    report = ExportReport(
        ListTransactions(repo), LoadPortfolioPositions(repo), None, writer, events=repo
    )
    assert report.execute("events", 1, "ignored.csv") == 1
    assert "100.00000001" in writer.content and "'=danger" in writer.content


def test_data_dir_preserves_checkout_and_uses_explicit_absolute_override(
    monkeypatch, tmp_path
):
    from nexo.core.paths import application_data_dir

    monkeypatch.setenv("NEXO_DATA_DIR", str(tmp_path))
    assert application_data_dir() == tmp_path.resolve()
    monkeypatch.setenv("NEXO_DATA_DIR", "relative")
    with pytest.raises(ValueError):
        application_data_dir()
    monkeypatch.delenv("NEXO_DATA_DIR")
    assert application_data_dir().name == "data"
    monkeypatch.setattr(__import__("sys"), "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert application_data_dir() == tmp_path / "NexoInvest"


def test_read_ledger_uses_one_database_transaction(ledger):
    from sqlalchemy import event as sql_event

    _, repo = ledger
    repo.add_event(event(amount="200"))
    RegisterTransaction(repo).execute(trade())
    statements = []
    engine = repo._session_factory.kw["bind"]

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.strip().upper())

    sql_event.listen(engine, "before_cursor_execute", record)
    try:
        trades, events = repo.read_ledger(1)
    finally:
        sql_event.remove(engine, "before_cursor_execute", record)
    assert statements[0] == "BEGIN"
    assert len(trades) == len(events) == 1
    assert cash_state(trades, events).balance == 100
