from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.ui.dialogs.transaction_dialog import (
    TransactionDialog as TransactionDialog,  # noqa: PLC0414 -- preserve public import
)


class PortfolioDialog(QDialog):
    """Submit a portfolio name and accept only after persistence succeeds."""

    portfolio_created = Signal(object)

    def __init__(
        self,
        create_portfolio: CreatePortfolio,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._create_portfolio = create_portfolio
        self.setObjectName("portfolio_dialog")
        self.setWindowTitle("Nova carteira")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        heading = QLabel("Nova carteira")
        heading.setObjectName("DialogTitle")
        layout.addWidget(heading)
        self.name_field = QLineEdit()
        self.name_field.setObjectName("portfolio_name")
        self.name_field.setPlaceholderText("Nome da carteira")
        form = QFormLayout()
        form.addRow("Nome", self.name_field)
        layout.addLayout(form)
        self.feedback = QLabel()
        self.feedback.setObjectName("WarningBadge")
        self.feedback.setWordWrap(True)
        self.feedback.hide()
        layout.addWidget(self.feedback)
        buttons = QDialogButtonBox()
        cancel = buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        cancel.setObjectName("SecondaryButton")
        self.save_button = buttons.addButton(
            "Criar carteira",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.save_button.setObjectName("PrimaryButton")
        buttons.rejected.connect(self.reject)
        self.save_button.clicked.connect(self._save)
        self.name_field.returnPressed.connect(self._save)
        layout.addWidget(buttons)

    def _save(self) -> None:
        self.save_button.setEnabled(False)
        try:
            portfolio = self._create_portfolio.execute(self.name_field.text())
        except ValueError as error:
            self.feedback.setText(str(error))
            self.feedback.show()
            self.name_field.setFocus()
        except PortfolioRepositoryError:
            self.feedback.setText(
                "Não foi possível salvar a carteira. Tente novamente."
            )
            self.feedback.show()
        else:
            self.portfolio_created.emit(portfolio)
            self.accept()
        finally:
            self.save_button.setEnabled(True)


class NoticeDialog(QDialog):
    def __init__(self, title: str, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("notice_dialog")
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        heading = QLabel(title)
        heading.setObjectName("DialogTitle")
        body = QLabel(message)
        body.setObjectName("SecondaryText")
        body.setWordWrap(True)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addWidget(close)
