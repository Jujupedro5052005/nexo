from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class NavigationButton(QPushButton):
    """Checkable sidebar button associated with one page."""

    def __init__(self, text: str, icon: QIcon, page_index: int) -> None:
        super().__init__(text)
        self.page_index = page_index
        self.setObjectName("NavigationButton")
        self.setAccessibleName(text)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setIcon(icon)
        self.setIconSize(QSize(19, 19))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
