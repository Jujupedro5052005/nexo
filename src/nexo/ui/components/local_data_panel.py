from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QLineEdit, QMessageBox

from nexo.application.local_data import ManageLocalData
from nexo.ui.components.common import SectionCard, action_button
from nexo.ui.workers import TaskRunner


class LocalDataPanel(SectionCard):
    data_cleared = Signal()
    reset_finished = Signal()

    def __init__(self, case: ManageLocalData | None) -> None:
        super().__init__("Dados locais")
        self.case = case
        self.prepare_reset: Callable[[], None] = lambda: None
        self.wait_reset: Callable[[], None] = lambda: None
        self.runner = TaskRunner(self)
        self.busy = False
        self.location = QLineEdit(
            case.location if case else "Banco local não conectado."
        )
        self.location.setReadOnly(True)
        self.location.setAccessibleName("Local do banco SQLite")
        self.location.setToolTip(self.location.text())
        self.export_button = action_button("Exportar dados")
        self.clear_button = action_button("Limpar dados")
        self.export_button.clicked.connect(self.export)
        self.clear_button.clicked.connect(self.clear)
        self.feedback = QLabel(
            "Exportação completa em SQLite. Limpeza cria uma cópia de segurança antes de remover registros."
        )
        self.feedback.setWordWrap(True)
        for widget in (
            self.location,
            self.export_button,
            self.clear_button,
            self.feedback,
        ):
            self.content.addWidget(widget)
        self.set_busy(False)

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.export_button.setEnabled(self.case is not None and not busy)
        self.clear_button.setEnabled(self.case is not None and not busy)

    def export(self) -> None:
        if self.case is None or self.busy:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar banco completo", "nexo_backup.db", "SQLite (*.db)"
        )
        if not path:
            return
        if not path.lower().endswith(".db"):
            path += ".db"
        case = self.case
        self.set_busy(True)
        self.runner.submit(
            lambda: case.export(path),
            lambda result, error: self.completed(result, error, path),
        )

    def completed(self, result: Any, error: Exception | None, path: str = "") -> None:
        self.set_busy(False)
        self.feedback.setText(
            "Não foi possível concluir a operação. Dados locais preservados."
            if error
            else f"Exportação salva em {path}"
            if path
            else f"Dados limpos. Cópia de segurança: {result}"
        )
        if not error and not path:
            self.data_cleared.emit()
        if not path:
            self.reset_finished.emit()

    def clear(self) -> None:
        if self.case is None or self.busy:
            return
        answer = QMessageBox.question(
            self,
            "Limpar dados locais",
            "Remover todas as carteiras, movimentações, eventos de caixa, planejamento, metas e alertas deste banco? Uma cópia SQLite será salva ao lado do banco antes da limpeza.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.prepare_reset()
        self.set_busy(True)
        self.feedback.setText("Aguardando consultas e preparando cópia de segurança…")
        case = self.case

        def reset() -> Any:
            self.wait_reset()
            return case.clear()

        self.runner.submit(reset, self.completed)
