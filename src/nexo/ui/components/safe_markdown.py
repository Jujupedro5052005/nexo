from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QTextBrowser


class SafeMarkdownBrowser(QTextBrowser):
    """Render generated prose without loading embedded local files or images."""

    def loadResource(self, resource_type: int, name: QUrl | str) -> Any:
        return None
