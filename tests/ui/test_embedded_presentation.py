import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage

from nexo.core.paths import resource_path
from nexo.ui.navigation import PageId
from nexo.ui.pages.presentation_page import PresentationPage


def javascript(qtbot, page, expression):
    results = []
    page.runJavaScript(expression, results.append)
    qtbot.waitUntil(lambda: bool(results), timeout=10000)
    return results[0]


def test_real_local_html_preserves_slide_focus_and_pause(qtbot):
    page = PresentationPage()
    qtbot.addWidget(page)
    page.resize(1000, 650)
    page.show()
    qtbot.waitUntil(lambda: page.loaded, timeout=30000)
    state = lambda: json.loads(javascript(qtbot, page.browser, "JSON.stringify(window.NexoPresentation.getState())"))
    assert state()["total"] == 14 and state()["embedded"]
    javascript(qtbot, page.browser, "window.NexoPresentation.goTo(4)")
    assert state()["slide"] == 4
    page.hide()
    assert state()["paused"]
    page.show()
    qtbot.waitUntil(lambda: page.web.hasFocus())
    assert state()["slide"] == 4 and not state()["paused"]
    qtbot.keyClick(page.web.focusProxy(), Qt.Key.Key_Right)
    qtbot.wait(400)
    assert state()["slide"] == 5
    with qtbot.waitSignal(page.demo_requested) as signal:
        javascript(qtbot, page.browser, "window.NexoPresentation.requestDemo()")
    assert signal.args == [5] and page.saved_slide == 5
    qtbot.wait(200)
    assert page.loaded and not page.error.isVisible()
    assert state()["slide"] == 5
    page.hide()
    page.show()
    assert state()["slide"] == 5
    assert not page.browser.acceptNavigationRequest(
        QUrl("nexo://presentation/fullscreen"),
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked, True,
    )
    assert page.window().isFullScreen()
    qtbot.keyClick(page.web.focusProxy(), Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not page.window().isFullScreen())
    assert not page.window().isFullScreen()
    assert not page.browser.acceptNavigationRequest(
        QUrl("https://example.com"), QWebEnginePage.NavigationType.NavigationTypeLinkClicked, True,
    )
    assert not page.browser.acceptNavigationRequest(
        QUrl.fromLocalFile(str(Path.home() / "private.txt")),
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked, True,
    )


def test_assets_and_build_keep_offline_resources():
    assert resource_path("icons", "Nexo_Icone.ico").is_file()
    assert resource_path("presentation", "Nexo_Apresentacao.html").is_file()
    spec = Path("Nexo.spec").read_text()
    assert '"PySide6.QtWebEngineWidgets"' not in spec.split("excludes=")[1]
    assert "Nexo_Icone.ico" in spec and '"knowledge"' in spec
    assert PageId.SETTINGS == 11 and PageId.PRESENTATION == 10


def test_tour_with_synchronous_host_navigation(qtbot):
    from PySide6.QtWidgets import QStackedWidget, QWidget

    stack = QStackedWidget()
    qtbot.addWidget(stack)
    stack.addWidget(QWidget())
    page = PresentationPage()
    stack.addWidget(page)
    page.demo_requested.connect(lambda _slide: stack.setCurrentIndex(0))
    stack.resize(1200, 800)
    stack.show()
    stack.setCurrentIndex(1)
    qtbot.waitUntil(lambda: page.loaded, timeout=30000)
    javascript(qtbot, page.browser, "window.NexoPresentation.goTo(4)")
    qtbot.keyClick(page.web.focusProxy(), Qt.Key.Key_Right)
    javascript(qtbot, page.browser, "window.NexoPresentation.goTo(4)")
    javascript(qtbot, page.browser, "window.NexoPresentation.requestDemo()")
    qtbot.wait(500)
    assert stack.currentIndex() == 0
    stack.setCurrentIndex(1)
    qtbot.wait(500)
    assert page.loaded and not page.error.isVisible()
    assert javascript(qtbot, page.browser, "window.NexoPresentation.getState().slide") == 4
    qtbot.keyClick(page.web.focusProxy(), Qt.Key.Key_F)
    qtbot.waitUntil(lambda: stack.isFullScreen())
    qtbot.keyClick(page.web.focusProxy(), Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not stack.isFullScreen())


def test_education_layout_and_existing_destinations(qtbot, portfolio_repository):
    from nexo.application.portfolio.create_portfolio import CreatePortfolio
    from nexo.application.portfolio.list_portfolios import ListPortfolios
    from nexo.main import create_application
    from nexo.ui.windows.main_window import MainWindow

    create_application()
    window = MainWindow(CreatePortfolio(portfolio_repository), ListPortfolios(portfolio_repository))
    qtbot.addWidget(window)
    window.show()
    window.show_page(PageId.ANALYSIS)
    window.analysis_page.tabs.setCurrentIndex(3)
    panel = window.analysis_page.workbench.diligence
    window.analysis_page.workbench.tabs.setCurrentIndex(3)
    for width, height in ((1180, 720), (1440, 900)):
        window.resize(width, height)
        qtbot.wait(150)
        assert panel.topic.y() < panel.companion.y()
        assert panel.companion.height() < 160
        assert panel.question_widget.y() - panel.companion.geometry().bottom() < 30
        output = Path("tmp/final-presentation")
        output.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(output / f"education-{width}.png"))
    panel.companion.help_button.click()
    assert window.page_stack.currentIndex() == PageId.INTELLIGENCE
    assert panel.topic.currentText() in window.intelligence_page.question.toPlainText()
    assert window.intelligence_page._response is None
    window.assets_page.integration_requested.emit()
    assert window.page_stack.currentIndex() == PageId.SETTINGS
