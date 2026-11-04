"""Restricted local slides: the only host commands are tour and fullscreen."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QUrlQuery, Signal
from PySide6.QtGui import (
    QDesktopServices,
    QHideEvent,
    QKeySequence,
    QShortcut,
    QShowEvent,
)
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from nexo.core.paths import resource_path


class LocalRequests(QWebEngineUrlRequestInterceptor):
    def __init__(self, document: Path, parent: QWidget) -> None:
        super().__init__(parent)
        self.document = document.resolve()

    def interceptRequest(self, info):
        url = info.requestUrl()
        allowed = url.scheme() in {"data", "blob"} or (
            url.isLocalFile() and Path(url.toLocalFile()).resolve() == self.document
        )
        info.block(not allowed)


class PresentationWebPage(QWebEnginePage):
    demo_requested = Signal(int)
    fullscreen_requested = Signal()

    def __init__(self, profile: QWebEngineProfile, document: Path, parent: QWidget):
        super().__init__(profile, parent)
        self.document = document.resolve()
        self.rejected_navigation = False

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if url.scheme() == "nexo" and url.host() == "presentation":
            self.rejected_navigation = True
            if url.path() == "/demo":
                try:
                    slide = int(QUrlQuery(url).queryItemValue("slide"))
                except ValueError:
                    return False
                if 1 <= slide <= 14:
                    self.demo_requested.emit(slide)
            elif url.path() == "/fullscreen":
                self.fullscreen_requested.emit()
            return False
        allowed = bool(url.isLocalFile() and Path(url.toLocalFile()).resolve() == self.document)
        self.rejected_navigation = not allowed
        return allowed

    def createWindow(self, window_type):
        return None


class PresentationPage(QWidget):
    demo_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("presentation_page")
        self.document = resource_path("presentation", "Nexo_Apresentacao.html")
        self.loaded = False
        self.started = False
        self.saved_slide = 1
        self.previous_state: Qt.WindowState | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.error = QWidget()
        error_layout = QVBoxLayout(self.error)
        error_layout.addWidget(QLabel("Não foi possível carregar a apresentação local. O restante do Nexo continua disponível."))
        for label, callback in (
            ("Tentar novamente", self.load),
            ("Abrir HTML externo", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.document)))),
            ("Abrir PDF de contingência", self.open_pdf),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            error_layout.addWidget(button)
        layout.addWidget(self.error)
        self.error.hide()
        self.profile = QWebEngineProfile(self)
        self.profile.downloadRequested.connect(lambda download: download.cancel())
        self.interceptor = LocalRequests(self.document, self)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.web = QWebEngineView(self)
        self.browser = PresentationWebPage(self.profile, self.document, self.web)
        self.web.setPage(self.browser)
        self.exit_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.web)
        self.exit_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.exit_shortcut.setEnabled(False)
        self.exit_shortcut.activated.connect(self.exit_fullscreen)
        settings = self.browser.settings()
        for attribute in (
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
        ):
            settings.setAttribute(attribute, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.browser.demo_requested.connect(self._demo)
        self.browser.fullscreen_requested.connect(self.toggle_fullscreen)
        self.browser.fullScreenRequested.connect(self._fullscreen_request)
        self.web.loadFinished.connect(self._finished)
        layout.addWidget(self.web, 1)

    def load(self) -> None:
        self.started = True
        self.browser.rejected_navigation = False
        self.error.hide()
        self.web.show()
        url = QUrl.fromLocalFile(str(self.document))
        query = QUrlQuery()
        query.addQueryItem("embedded", "1")
        url.setQuery(query)
        self.web.load(url)

    def _finished(self, success: bool) -> None:
        # Qt emits loadFinished(False) even when the host deliberately cancels
        # a nexo:// navigation. The already loaded document is still healthy.
        if not success and self.loaded and self.browser.rejected_navigation:
            self.browser.rejected_navigation = False
            return
        self.loaded = success
        self.error.setVisible(not success)
        self.web.setVisible(success)
        if success:
            self.browser.runJavaScript("window.NexoPresentation." + ("resume()" if self.isVisible() else "pause()"))
            self.web.setFocus()

    def _demo(self, slide: int) -> None:
        self.saved_slide = slide
        self.exit_fullscreen()
        self.demo_requested.emit(slide)

    def set_fullscreen(self, enabled: bool) -> None:
        window = self.window()
        if enabled and self.previous_state is None:
            self.previous_state = window.windowState()
            self.exit_shortcut.setEnabled(True)
            title = getattr(window, "_nexo_title_bar", None)
            if title is not None:
                title.hide()
            window.showFullScreen()
        elif not enabled and self.previous_state is not None:
            window.setWindowState(self.previous_state)
            self.previous_state = None
            self.exit_shortcut.setEnabled(False)
            title = getattr(window, "_nexo_title_bar", None)
            if title is not None:
                title.show()

    def toggle_fullscreen(self) -> None:
        self.set_fullscreen(self.previous_state is None)

    def exit_fullscreen(self) -> None:
        if self.previous_state is not None:
            self.browser.triggerAction(QWebEnginePage.WebAction.ExitFullScreen)
            self.set_fullscreen(False)

    def _fullscreen_request(self, request) -> None:
        request.accept()
        self.set_fullscreen(request.toggleOn())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self.started:
            self.load()
        elif self.loaded:
            self.browser.runJavaScript("window.NexoPresentation.resume()")
        self.web.setFocus()

    def hideEvent(self, event: QHideEvent) -> None:
        if self.loaded:
            self.browser.runJavaScript("window.NexoPresentation.pause()")
        self.exit_fullscreen()
        super().hideEvent(event)

    def open_pdf(self) -> None:
        path = resource_path("presentation", "Nexo_Apresentacao_Final_Revisada.pdf")
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
