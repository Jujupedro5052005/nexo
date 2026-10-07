from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QBoxLayout, QSizePolicy, QWidget


class ResponsivePair(QWidget):
    """Two cards in one aligned row, stacked below a content-width breakpoint."""

    def __init__(
        self, left: QWidget, right: QWidget, *, breakpoint: int = 1000,
        stretches: tuple[int, int] = (3, 1),
    ) -> None:
        super().__init__()
        self.setObjectName("ResponsivePair")
        self.breakpoint = breakpoint
        self.stretches = stretches
        self.row = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(14)
        self.row.addWidget(left, stretches[0])
        self.row.addWidget(right, stretches[1])
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

    def resizeEvent(self, event: QResizeEvent) -> None:
        stacked = event.size().width() < self.breakpoint
        direction = QBoxLayout.Direction.TopToBottom if stacked else QBoxLayout.Direction.LeftToRight
        if self.row.direction() != direction:
            self.row.setDirection(direction)
            for index, stretch in enumerate(self.stretches):
                self.row.setStretch(index, 0 if stacked else stretch)
            self.updateGeometry()
        super().resizeEvent(event)
