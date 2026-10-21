from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)


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
        self.setToolTip(tooltip or detail or label)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)
        top = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setToolTip(tooltip or detail or label)
        label_widget.setObjectName("MetricLabel")
        label_widget.setWordWrap(True)
        top.addWidget(label_widget, 1)
        help_widget = QToolButton()
        help_widget.setText("?")
        help_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        help_widget.setAccessibleName(f"Explicar {label}")
        help_widget.clicked.connect(
            lambda: QToolTip.showText(
                help_widget.mapToGlobal(help_widget.rect().bottomLeft()),
                help_widget.toolTip(),
                help_widget,
            )
        )
        help_widget.setObjectName("SecondaryText")
        help_widget.setToolTip(tooltip or detail or label)
        top.addWidget(help_widget)
        if icon is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(18, 18)))
            top.addWidget(icon_label)
        value_widget = QLabel(value)
        value_widget.setObjectName("MetricValue")
        self.value_label = value_widget
        value_widget.setAccessibleName(label)
        self.detail_label = QLabel(detail)
        detail_widget = self.detail_label
        detail_widget.setWordWrap(True)
        detail_widget.setObjectName(
            "Positive"
            if trend == "positive"
            else "Negative"
            if trend == "negative"
            else "MetricDetail"
        )
        layout.addLayout(top)
        layout.addWidget(value_widget)
        layout.addWidget(detail_widget)

    def set_value(self, text: str, state: str = "neutral") -> None:
        self.value_label.setText(text)
        self.value_label.setProperty("metricState", state)
        self.value_label.style().unpolish(self.value_label)
        self.value_label.style().polish(self.value_label)
