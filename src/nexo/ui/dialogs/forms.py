from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.ui.components.common import Badge
from nexo.ui.dialogs.transaction_dialog import (
    TransactionDialog as TransactionDialog,  # noqa: PLC0414 -- preserve public import
)


class DemoFormDialog(QDialog):
    """Shared dialog chrome and presentation-only save feedback."""

    def __init__(
        self, title: str, object_name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(540)
        self.dialog_layout = QVBoxLayout(self)
        self.dialog_layout.setContentsMargins(26, 24, 26, 24)
        self.dialog_layout.setSpacing(16)
        heading = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("DialogTitle")
        heading.addWidget(title_label)
        heading.addStretch()
        heading.addWidget(Badge("Demonstração", "DemoBadge"))
        self.dialog_layout.addLayout(heading)
        self.form = QFormLayout()
        self.form.setSpacing(11)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.dialog_layout.addLayout(self.form)
        self.feedback = QLabel(
            "Demonstração: persistência será conectada posteriormente."
        )
        self.feedback.setObjectName("WarningBadge")
        self.feedback.setWordWrap(True)
        self.feedback.setVisible(False)

    def add_buttons(self, save_text: str) -> None:
        self.dialog_layout.addWidget(self.feedback)
        buttons = QDialogButtonBox()
        cancel = buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        save = buttons.addButton(save_text, QDialogButtonBox.ButtonRole.AcceptRole)
        cancel.setObjectName("SecondaryButton")
        save.setObjectName("PrimaryButton")
        buttons.rejected.connect(self.reject)
        save.clicked.connect(lambda: self.feedback.setVisible(True))
        self.dialog_layout.addWidget(buttons)

    @staticmethod
    def text_field(placeholder: str = "") -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        return field

    @staticmethod
    def combo(items: list[str]) -> QComboBox:
        field = QComboBox()
        field.addItems(items)
        return field


class AssetDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Adicionar ativo", "asset_dialog", parent)
        self.form.addRow("Buscar ativo", self.text_field("Código ou nome"))
        self.form.addRow("Símbolo", self.text_field("Ex.: PETR4"))
        self.form.addRow("Nome", self.text_field("Nome do ativo"))
        self.form.addRow(
            "Tipo",
            self.combo(["Ação", "FII", "ETF", "Renda fixa", "Cripto", "Internacional"]),
        )
        self.form.addRow("Preço atual", self.text_field("R$ 0,00"))
        self.form.addRow("Moeda", self.combo(["BRL", "USD", "EUR"]))
        self.add_buttons("Adicionar ativo")


class AlertDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Criar alerta", "alert_dialog", parent)
        self.form.addRow("Ativo", self.text_field("Ex.: PETR4"))
        self.form.addRow(
            "Condição",
            self.combo(["Preço abaixo de", "Preço acima de", "Variação percentual"]),
        )
        self.form.addRow("Valor alvo", self.text_field("R$ 0,00"))
        self.form.addRow("Canal", self.combo(["No aplicativo"]))
        channels = QLabel("E-mail  Em breve    •    WhatsApp  Em breve")
        channels.setObjectName("MutedBadge")
        self.dialog_layout.addWidget(channels)
        self.add_buttons("Criar alerta")


class GoalDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Criar meta", "goal_dialog", parent)
        self.form.addRow("Nome da meta", self.text_field("Ex.: Reserva de emergência"))
        self.form.addRow(
            "Categoria",
            self.combo(["Segurança", "Patrimônio", "Experiência", "Educação", "Outro"]),
        )
        self.form.addRow("Valor alvo", self.text_field("R$ 0,00"))
        self.form.addRow("Valor atual", self.text_field("R$ 0,00"))
        deadline = QDateEdit(QDate.currentDate().addYears(1))
        deadline.setCalendarPopup(True)
        deadline.setDisplayFormat("dd/MM/yyyy")
        self.form.addRow("Prazo", deadline)
        self.form.addRow("Prioridade", self.combo(["Alta", "Média", "Baixa"]))
        preview = QLabel("Preview de progresso  0%")
        preview.setObjectName("Badge")
        self.dialog_layout.addWidget(preview)
        self.add_buttons("Criar meta")


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
