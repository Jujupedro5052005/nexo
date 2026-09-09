from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MetricCard(QFrame):
    """A compact KPI with icon, value and contextual detail."""

    def __init__(
        self,
        label: str,
        value: str,
        detail: str = "",
        icon: QIcon | None = None,
        trend: str = "neutral",
        tooltip: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(116)
        self.setToolTip(tooltip)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)
        top = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setObjectName("MetricLabel")
        top.addWidget(label_widget)
        top.addStretch()
        if icon is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(18, 18)))
            top.addWidget(icon_label)
        value_widget = QLabel(value)
        value_widget.setObjectName("MetricValue")
        detail_widget = QLabel(detail)
        detail_widget.setObjectName(
            "Positive" if trend == "positive" else "Negative" if trend == "negative" else "MetricDetail"
        )
        layout.addLayout(top)
        layout.addWidget(value_widget)
        layout.addWidget(detail_widget)
