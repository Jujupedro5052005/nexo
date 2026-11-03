from threading import Event

from PySide6.QtCore import QTimer

from nexo.domain.models.intelligence import AnalysisResponse
from nexo.ui.pages.intelligence_page import IntelligencePage


def test_ui_offline_chat_persistence_and_results(qtbot, workspace):
    page = IntelligencePage(workspace)
    qtbot.addWidget(page)
    page.question.setPlainText("Olá, explique o contexto")
    page.ask()
    qtbot.waitUntil(lambda: not page._busy)
    assert "Olá, explique" in page.chat.toPlainText()
    assert "offline" in page.feedback.text()
    assert page.export_button.isEnabled()
    page._new_conversation()
    assert not page.export_button.isEnabled()
    assert page._response is None
    page.runner.stop()
    page.runner.wait()


def test_cancel_keeps_gui_responsive_and_suppresses_late_result(qtbot, workspace):
    entered, release = Event(), Event()

    def blocked(request):
        entered.set()
        assert release.wait(5)
        return AnalysisResponse(markdown="Resposta atrasada", mode="test")

    workspace.orchestrator.ask = blocked
    page = IntelligencePage(workspace)
    qtbot.addWidget(page)
    page.question.setPlainText("Teste cancelamento")
    page.ask()
    qtbot.waitUntil(entered.is_set)
    ticks = []
    timer = QTimer(page)
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start(5)
    qtbot.waitUntil(lambda: len(ticks) >= 3)
    page.cancel()
    release.set()
    page.runner.wait()
    qtbot.wait(20)
    assert "Resposta atrasada" not in page.chat.toPlainText()
    assert not page._busy
    assert not page.export_button.isEnabled()
    page.runner.stop()


def test_ui_invalid_json_and_disabled_composition(qtbot, workspace):
    page = IntelligencePage(workspace)
    qtbot.addWidget(page)
    page.question.setPlainText("test")
    page.advanced.setChecked(True)
    page.assumptions.setPlainText("not JSON")
    page.ask()
    assert "JSON" in page.feedback.text()
    assert not page._busy
    absent = IntelligencePage()
    qtbot.addWidget(absent)
    assert not absent.send.isEnabled()


def test_premise_form_accepts_local_numbers_and_converts_display_percentages(
    qtbot, workspace
):
    page = IntelligencePage(workspace)
    qtbot.addWidget(page)
    page.method.setCurrentIndex(1)
    for key, value in {
        "expected_dividend": "3,00",
        "required_return": "10",
        "growth": "-2",
        "safety_discount": "20",
        "dividend_source": "Cenário manual",
        "sustainability_note": "Hipótese educacional",
    }.items():
        page.premise_fields[key].setText(value)
    assumptions = page._read_assumptions()
    assert assumptions["expected_dividend"] == "3.00"
    assert assumptions["required_return"] == "0.1"
    assert assumptions["growth"] == "-0.02"
    assert assumptions["safety_discount"] == "0.2"
    page.method.setCurrentIndex(3)
    assert page._read_assumptions()["metric"] == "eps"
    assert "expected_dividend" not in page._read_assumptions()


def test_markdown_never_loads_embedded_files(qtbot):
    from PySide6.QtCore import QUrl

    from nexo.ui.components.safe_markdown import SafeMarkdownBrowser

    browser = SafeMarkdownBrowser()
    qtbot.addWidget(browser)
    assert browser.loadResource(2, QUrl("file:///sensitive.txt")) is None
    assert browser.loadResource(2, QUrl("https://example.org/image.png")) is None
