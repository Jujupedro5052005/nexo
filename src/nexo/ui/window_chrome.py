"""Windows identity and native caption, with a system-resizable Qt fallback."""

import ctypes
import sys
from ctypes import wintypes
from typing import Any, cast

from PySide6.QtCore import QAbstractNativeEventFilter, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def set_app_user_model_id() -> None:
    if sys.platform == "win32":
        function = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        function.argtypes = [wintypes.LPCWSTR]
        function.restype = ctypes.c_long
        if function("NexoInvest.Desktop") < 0:
            raise OSError("Não foi possível configurar a identidade da janela.")


def native_caption(window: QWidget) -> bool:
    if sys.platform != "win32":
        return True
    if sys.getwindowsversion().build < 22000:
        return False
    function = ctypes.windll.dwmapi.DwmSetWindowAttribute
    function.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    function.restype = ctypes.c_long
    results = []
    # COLORREF stores red in the low byte: #07111F -> 0x1F1107.
    for attribute, value in ((20, 1), (35, 0x1F1107), (36, 0xFAF7F5)):
        color = wintypes.DWORD(value)
        results.append(function(int(window.winId()), attribute, ctypes.byref(color), ctypes.sizeof(color)))
    return all(result >= 0 for result in results)


class ResizeFilter(QAbstractNativeEventFilter):
    """Delegate all eight window edges to the Windows sizing loop."""

    def __init__(self, window: QWidget) -> None:
        super().__init__()
        self.window = window

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        window = self.window
        if msg.message not in (0x0084, 0x00A1):
            return False, 0
        # Showing WebEngine can recreate the HWND to change the window surface.
        # Query only for hit tests, after Qt has created the native window.
        if msg.hWnd != int(window.winId()):
            return False, 0
        if window.isMaximized() or window.isFullScreen():
            return False, 0
        if msg.message == 0x00A1:  # WM_NCLBUTTONDOWN
            edges = {
                10: Qt.Edge.LeftEdge,
                11: Qt.Edge.RightEdge,
                12: Qt.Edge.TopEdge,
                13: Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
                14: Qt.Edge.TopEdge | Qt.Edge.RightEdge,
                15: Qt.Edge.BottomEdge,
                16: Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
                17: Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
            }.get(msg.wParam)
            handle = window.windowHandle()
            if edges is not None and handle is not None:
                return bool(handle.startSystemResize(edges)), 0
            return False, 0
        point = window.mapFromGlobal(QCursor.pos())
        left, right = point.x() < 6, point.x() >= window.width() - 6
        top, bottom = point.y() < 6, point.y() >= window.height() - 6
        result = (13 if left else 14 if right else 12) if top else (16 if left else 17 if right else 15) if bottom else 10 if left else 11 if right else 0
        return (True, result) if result else (False, 0)


class TitleBar(QWidget):
    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self.host = window
        self.setObjectName("NexoTitleBar")
        self.setStyleSheet("#NexoTitleBar {background:#07111F;} #NexoTitleBar QLabel {color:#F5F7FA;} #NexoTitleBar QPushButton {background:#07111F;color:#F5F7FA;border:0;border-radius:0;padding:6px 14px;min-height:18px;} #NexoTitleBar QPushButton:hover {background:#243247;}")
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 4, 4)
        mark = QLabel()
        mark.setPixmap(window.windowIcon().pixmap(20, 20))
        row.addWidget(mark)
        title = QLabel(window.windowTitle())
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(title, 1)
        window.windowTitleChanged.connect(title.setText)
        for text, name, callback in (
            ("—", "Minimizar", window.showMinimized),
            ("□", "Maximizar ou restaurar", self.toggle_maximized),
            ("×", "Fechar", window.close),
        ):
            button = QPushButton(text)
            button.setAccessibleName(name)
            button.setToolTip(name)
            button.clicked.connect(callback)
            row.addWidget(button)

    def toggle_maximized(self) -> None:
        self.host.showNormal() if self.host.isMaximized() else self.host.showMaximized()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.host.windowHandle()
            if handle is not None:
                handle.startSystemMove()


def install_window_chrome(window: QWidget) -> None:
    window.setWindowIcon(QApplication.windowIcon())
    if native_caption(window):
        return
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    title = TitleBar(window)
    if isinstance(window, QMainWindow):
        window.setMenuWidget(title)
    else:
        cast(QVBoxLayout, window.layout()).insertWidget(0, title)
    resize_filter = ResizeFilter(window)
    app = cast(QApplication, QApplication.instance())
    app.installNativeEventFilter(resize_filter)
    window.destroyed.connect(lambda: app.removeNativeEventFilter(resize_filter))
    cast(Any, window)._nexo_resize_filter = resize_filter
    cast(Any, window)._nexo_title_bar = title

