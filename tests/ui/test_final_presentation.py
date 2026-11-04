import os
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel
from test_demo_presentation import PresentationTestProvider

from nexo.core.paths import bundled_knowledge_dir, environment_file, resource_path
from nexo.infrastructure.database.demo_finances import seed_demo_finances
from nexo.infrastructure.database.repositories.personal_finance import (
    SqlPersonalFinanceRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from nexo.ui.components.companion import CompanionCard, CompanionState
from nexo.ui.dialogs.startup import StartupDialog
from nexo.ui.windows.main_window import PAGE_INFO, MainWindow


def test_demo_seed_is_idempotent_and_refuses_normal_database(tmp_path):
    demo = create_database_engine(tmp_path / "nexo_demo.db")
    normal = create_database_engine(tmp_path / "nexo.db")
    try:
        for engine in (demo, normal):
            initialize_database(engine)
        seed_demo_finances(demo)
        repo = SqlPersonalFinanceRepository(create_session_factory(demo))
        assert (len(repo.budget_entries()), len(repo.goals()), len(repo.alerts())) == (
            4,
            3,
            3,
        )
        before = repo.budget_entries(), repo.goals(), repo.alerts()
        seed_demo_finances(demo)
        assert (repo.budget_entries(), repo.goals(), repo.alerts()) == before
        assert all(
            e.month.month == datetime.now().astimezone().month
            for e in repo.budget_entries()
        )
        with pytest.raises(ValueError):
            seed_demo_finances(normal)
        assert (
            SqlPersonalFinanceRepository(create_session_factory(normal)).goals() == ()
        )
    finally:
        demo.dispose()
        normal.dispose()


def test_companion_reacts_and_stops_animation_when_hidden_or_reduced(qtbot):
    card = CompanionCard()
    qtbot.addWidget(card)
    card.show()
    card.set_state(CompanionState.ANALYZING, "Consultando evidências")
    assert card.avatar.timer.isActive()
    card.motion.setChecked(False)
    assert not card.avatar.timer.isActive()
    card.motion.setChecked(True)
    assert card.avatar.timer.isActive()
    card.hide()
    assert not card.avatar.timer.isActive()
    card.show()
    card.set_state(CompanionState.COMPLETE, "Pronto para revisão")
    assert not card.avatar.timer.isActive() and "Pronto" in card.message.text()


def test_frozen_paths_use_bundle_resources_and_external_secrets(monkeypatch, tmp_path):
    from nexo.core import paths

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        paths.sys, "_MEIPASS", str(tmp_path / "_internal"), raising=False
    )
    monkeypatch.setattr(paths.sys, "executable", str(tmp_path / "Nexo.exe"))
    assert environment_file() == tmp_path / ".env"
    assert bundled_knowledge_dir() == tmp_path / "_internal" / "knowledge"
    assert resource_path("icons", "Nexo_Icone.ico") == tmp_path / "_internal/nexo/resources/icons/Nexo_Icone.ico"


def test_cancel_startup_creates_no_database_or_provider(qtbot, monkeypatch, tmp_path):
    import nexo.main as entry

    monkeypatch.setenv("NEXO_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(entry, "choose_startup_mode", lambda: None)
    monkeypatch.setattr(
        entry,
        "ProviderServices",
        lambda *a: pytest.fail("Cancelled startup composed a provider"),
    )
    assert entry.main() == 0
    assert not list(tmp_path.glob("*.db"))


@pytest.mark.parametrize("size", [(1440, 900), (1180, 720)])
@pytest.mark.parametrize("demo_mode", [True, False])
def test_visual_entry_without_flags_and_guided_pages(
    qtbot, qapp, monkeypatch, tmp_path, size, demo_mode
):
    import nexo.main as entry
    import nexo.ui.preferences as preference_module

    monkeypatch.setenv("NEXO_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NEXO_AI_PROVIDER", "mock")
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(preference_module, "preferences", lambda: settings)
    provider = PresentationTestProvider()
    monkeypatch.setattr(
        entry,
        "ProviderServices",
        lambda *a: SimpleNamespace(
            yahoo=provider,
            market=provider,
            fundamentals=provider,
            dividends=provider,
            official=None,
            actions=None,
            health=lambda: (),
            close=lambda: None,
        ),
    )
    app = entry.create_application()
    saved_font = app.font()
    app.setFont(QFont("Segoe UI", 9))
    output = Path(os.environ.get("NEXO_FINAL_REVIEW_DIR", str(tmp_path / "captures")))
    output.mkdir(parents=True, exist_ok=True)

    def capture(name, widget):
        qtbot.wait(30)
        assert widget.grab().save(str(output / f"{name}-{size[0]}.png"))

    def choose():
        dialog = next(
            w
            for w in app.topLevelWidgets()
            if isinstance(w, StartupDialog) and w.isVisible()
        )
        qtbot.addWidget(dialog)
        capture("startup", dialog)
        (dialog.demo_button if demo_mode else dialog.normal_button).click()

    def run():
        window = next(
            w
            for w in app.topLevelWidgets()
            if isinstance(w, MainWindow) and w.isVisible()
        )
        qtbot.addWidget(window)
        window.resize(*size)
        assert PAGE_INFO[-1][0] == "Configurações"
        assert window.navigation_buttons[-1].text() == "Configurações"
        assert window.demo_mode == demo_mode
        assert ("DEMO" in window.mode_badge.text()) == demo_mode
        if not demo_mode:
            assert window.selected_portfolio_id is None
            assert not (tmp_path / "nexo_demo.db").exists()
            window.close()
            return 0
        assert not (tmp_path / "nexo.db").exists()
        window.show_page(4)
        assert len(window.planning_page.entries) == 4
        window.planning_page.scenario.calculate()
        assert "Capital projetado" in window.planning_page.scenario.result.text()
        capture("planning", window)
        window.planning_page.scenario.allocate()
        assert "450,00" in window.planning_page.scenario.allocation_result.text()
        window.planning_page.scenario_button.click()
        capture("planning-scenario", window)
        window.show_page(5)
        assert window.goals_page.table.rowCount() == 3
        capture("goals", window)
        window.show_page(6)
        assert window.alerts_page.table.rowCount() == 3
        capture("alerts", window)
        window.show_page(7)
        window.analysis_page.tabs.setCurrentIndex(2)
        capture("performance", window)
        window.analysis_page.performance_panel.prepare_requested.emit()
        assert (
            window.page_stack.currentIndex() == 3
            and window.account_panel.details.isVisible()
        )
        window.show_page(7)
        window.analysis_page.tabs.setCurrentIndex(3)
        bench = window.analysis_page.workbench
        bench.tabs.setCurrentIndex(3)
        capture("education", window)
        bench.diligence.explain()
        assert window.page_stack.currentIndex() == 9
        page = window.intelligence_page
        assert "Explique" in page.question.toPlainText()
        page.context_toggle.setChecked(True)
        page.method.setCurrentIndex(1)
        capture("context", page.context_dialog)
        assert page.context_dialog.width() >= 580
        page._new_conversation()
        assert not page.context_dialog.isVisible()
        assert page.chat_splitter.count() == 1
        capture("new-conversation", window)
        page.tabs.setCurrentIndex(1)
        assert page.report_view.findChildren(QLabel)
        capture("report-empty", window)
        page.tabs.setCurrentIndex(0)
        page.method.setCurrentIndex(0)
        page.question.setPlainText("Analise toda a minha carteira")
        page.ask()
        qtbot.waitUntil(lambda: page._response is not None, timeout=15000)
        assert len(page.report_view.report["assets"]) == 8
        assert page.companion.avatar.state == CompanionState.COMPLETE
        page.tabs.setCurrentIndex(1)
        capture("report", window)
        window.show_page(8)
        window.reports_page.tabs.setCurrentIndex(1)
        panel = window.reports_page.tax_panel
        panel.load()
        assert panel.table.rowCount() == 12
        capture("tax-ledger", window)
        for key, value in {
            "profit": "1000",
            "loss": "200",
            "rate": "15",
            "withholding": "5",
        }.items():
            panel.inputs[key].setText(value)
        panel.calculate()
        panel.tabs.setCurrentIndex(1)
        assert "115,00" in panel.result.text()
        capture("tax", window)
        window.show_page(11)
        assert window.page_title.text() == "Configurações"
        window.close()
        return 0

    monkeypatch.setattr(app, "exec", run)
    QTimer.singleShot(0, choose)
    try:
        assert entry.main() == 0
    finally:
        app.setFont(saved_font)
