from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)


class Badge(QLabel):
    def __init__(self, text: str, kind: str = "Badge") -> None:
        super().__init__(text)
        self.setObjectName(kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(self.sizePolicy().Policy.Maximum, self.sizePolicy().Policy.Fixed)


class SectionCard(QFrame):
    def __init__(self, title: str = "", action: str | None = None) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(18, 16, 18, 18)
        self.content.setSpacing(12)
        if title:
            header = QHBoxLayout()
            title_label = QLabel(title)
            title_label.setObjectName("SectionTitle")
            header.addWidget(title_label)
            header.addStretch()
            if action:
                self.action_button = QPushButton(action)
                self.action_button.setObjectName("LinkButton")
                self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
                connect_planned_action(self.action_button)
                header.addWidget(self.action_button)
            self.content.addLayout(header)


class PageContent(QScrollArea):
    def __init__(self, page_key: str) -> None:
        super().__init__()
        self.setObjectName(f"{page_key}_page")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("PageContent")
        self.page_layout = QVBoxLayout(body)
        self.page_layout.setContentsMargins(28, 22, 28, 30)
        self.page_layout.setSpacing(16)
        self.setWidget(body)


class DataTable(QTableWidget):
    def __init__(self, headers: Iterable[str], rows: Iterable[Iterable[str]]) -> None:
        headers_list = list(headers)
        rows_list = [list(row) for row in rows]
        super().__init__(len(rows_list), len(headers_list))
        self.setHorizontalHeaderLabels(headers_list)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setMinimumHeight(54 + 42 * len(rows_list))
        for row_index, row in enumerate(rows_list):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                self.setItem(row_index, column_index, item)


class GoalProgress(QWidget):
    def __init__(self, name: str, current: str, target: str, progress: int) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(7)
        header = QHBoxLayout()
        title = QLabel(name)
        title.setObjectName("SectionTitle")
        amount = QLabel(f"{current} de {target}")
        amount.setObjectName("SecondaryText")
        percent = QLabel(f"{progress}%")
        percent.setObjectName("AccentText")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(amount)
        header.addWidget(percent)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)
        layout.addLayout(header)
        layout.addWidget(bar)


def action_button(text: str, primary: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("PrimaryButton" if primary else "SecondaryButton")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def connect_planned_action(
    button: QPushButton,
    message: str = "Esta funcionalidade será conectada ao domínio em uma próxima etapa.",
) -> None:
    button.setToolTip(message)
    button.clicked.connect(
        lambda: QToolTip.showText(
            button.mapToGlobal(button.rect().bottomLeft()), message, button
        )
    )


def filter_buttons(labels: Iterable[str]) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(7)
    for index, label in enumerate(labels):
        button = QPushButton(label)
        button.setObjectName("FilterButton")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setChecked(index == 0)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(button)
    layout.addStretch()
    return layout
