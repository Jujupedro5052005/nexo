from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyState(QWidget):
    """Consistent empty state with an optional action."""

    action_requested = Signal()

    def __init__(
        self,
        title: str,
        description: str,
        action_text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("EmptyTitle")
        description_label = QLabel(description)
        description_label.setObjectName("EmptyDescription")
        description_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(description_label)

        if action_text:
            action = QPushButton(action_text)
            action.setObjectName("PrimaryButton")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.clicked.connect(self.action_requested)
            layout.addSpacing(7)
            layout.addWidget(action, alignment=Qt.AlignmentFlag.AlignLeft)
