"""Small vector companion: presentation state only, no financial decisions."""

import math
from enum import Enum

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QHideEvent, QPainter, QPen, QShowEvent
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nexo.ui.components.common import SectionCard, action_button


class CompanionState(str, Enum):
    READY = "Pronto"
    ANALYZING = "Analisando"
    COMPLETE = "Concluído"
    ALERT = "Atenção"
    EXPLAINING = "Explicando"


class CompanionAvatar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(64, 64)
        self.state = CompanionState.READY
        self.motion = True
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)
        self.setAccessibleName("Copiloto financeiro Nexo")

    def _tick(self) -> None:
        self.phase = (self.phase + 0.12) % (2 * math.pi)
        self.update()

    def set_state(self, state: CompanionState) -> None:
        self.state = state
        self.setAccessibleDescription(state.value)
        self._sync()
        self.update()

    def _sync(self) -> None:
        if self.isVisible() and self.motion and self.state == CompanionState.ANALYZING:
            self.timer.start()
        else:
            self.timer.stop()

    def hideEvent(self, event: QHideEvent) -> None:
        self.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._sync()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#F5B95F" if self.state == CompanionState.ALERT else "#10C7C7")
        painter.setPen(QPen(color, 1.6))
        painter.setBrush(QColor("#102D3D"))
        painter.drawRoundedRect(QRectF(7, 9, 50, 46), 16, 16)
        pupil = 2 * math.sin(self.phase) if self.timer.isActive() else 0
        painter.setBrush(color)
        painter.drawEllipse(QRectF(20 + pupil, 25, 5, 6))
        painter.drawEllipse(QRectF(39 + pupil, 25, 5, 6))
        painter.drawLine(
            24, 42, 32, 45 if self.state == CompanionState.COMPLETE else 42
        )
        painter.drawLine(
            32, 45 if self.state == CompanionState.COMPLETE else 42, 41, 38
        )
        if self.timer.isActive():
            painter.drawArc(
                QRectF(2, 3, 60, 58), int(self.phase * 180 / math.pi * 16), 90 * 16
            )
        painter.end()


class CompanionCard(SectionCard):
    help_requested = Signal()

    def __init__(
        self,
        message: str = "Escolha uma carteira ou pergunte sobre um ativo. Eu ajudo a organizar a análise.",
    ) -> None:
        super().__init__()
        row = QHBoxLayout()
        self.avatar = CompanionAvatar()
        row.addWidget(self.avatar)
        text = QVBoxLayout()
        self.heading = QLabel("NEXO · seu copiloto financeiro")
        self.heading.setObjectName("SectionTitle")
        self.message = QLabel(message)
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        text.addWidget(self.heading)
        text.addWidget(self.message)
        row.addLayout(text, 1)
        controls = QVBoxLayout()
        self.help_button = action_button("Como começar")
        self.help_button.clicked.connect(self.help_requested)
        controls.addWidget(self.help_button)
        self.motion = QCheckBox("Animar")
        self.motion.setChecked(True)
        self.motion.setToolTip(
            "Desative para reduzir movimento. Animação só durante análise visível."
        )
        self.motion.toggled.connect(self._motion_changed)
        controls.addWidget(self.motion)
        row.addLayout(controls)
        self.content.addLayout(row)

    def _motion_changed(self, enabled: bool) -> None:
        self.avatar.motion = enabled
        self.avatar._sync()

    def set_state(self, state: CompanionState, message: str) -> None:
        self.avatar.set_state(state)
        self.heading.setText("NEXO · " + state.value)
        self.message.setText(message)


class GuideCard(SectionCard):
    def __init__(self, title: str, description: str, steps: str) -> None:
        super().__init__(title)
        for value in (description, steps):
            label = QLabel(value)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            self.content.addWidget(label)
