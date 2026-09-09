from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nexo.ui.components.common import Badge


class DemoFormDialog(QDialog):
    """Shared dialog chrome and presentation-only save feedback."""

    def __init__(self, title: str, object_name: str, parent: QWidget | None = None) -> None:
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
        self.feedback = QLabel("Demonstração: persistência será conectada posteriormente.")
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


class TransactionDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Nova movimentação", "transaction_dialog", parent)
        self.form.addRow("Carteira", self.combo(["Longo Prazo", "Reserva", "Internacional"]))
        self.form.addRow("Tipo", self.combo(["Compra", "Venda", "Aporte", "Retirada", "Provento"]))
        self.form.addRow("Ativo", self.text_field("Ex.: PETR4"))
        self.quantity = self.text_field("0")
        self.unit_price = self.text_field("R$ 0,00")
        self.fees = self.text_field("R$ 0,00")
        for field in (self.quantity, self.unit_price, self.fees):
            field.textChanged.connect(self.update_summary)
        self.form.addRow("Quantidade", self.quantity)
        self.form.addRow("Preço unitário", self.unit_price)
        date = QDateEdit(QDate.currentDate())
        date.setCalendarPopup(True)
        date.setDisplayFormat("dd/MM/yyyy")
        self.form.addRow("Data", date)
        self.form.addRow("Taxas", self.fees)
        notes = QTextEdit()
        notes.setPlaceholderText("Observações opcionais")
        notes.setMaximumHeight(70)
        self.form.addRow("Observações", notes)
        self.summary = QLabel("Valor bruto  R$ 0,00  •  Taxas  R$ 0,00  •  Valor total  R$ 0,00")
        self.summary.setObjectName("Badge")
        self.dialog_layout.addWidget(self.summary)
        self.add_buttons("Salvar movimentação")

    def update_summary(self) -> None:
        gross = self._decimal(self.quantity.text()) * self._decimal(self.unit_price.text())
        fees = self._decimal(self.fees.text())
        self.summary.setText(
            f"Valor bruto  R$ {gross:,.2f}  •  Taxas  R$ {fees:,.2f}  •  Valor total  R$ {gross + fees:,.2f}"
        )

    @staticmethod
    def _decimal(value: str) -> Decimal:
        normalized = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return Decimal(normalized or "0")
        except InvalidOperation:
            return Decimal(0)


class AssetDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Adicionar ativo", "asset_dialog", parent)
        self.form.addRow("Buscar ativo", self.text_field("Código ou nome"))
        self.form.addRow("Símbolo", self.text_field("Ex.: PETR4"))
        self.form.addRow("Nome", self.text_field("Nome do ativo"))
        self.form.addRow("Tipo", self.combo(["Ação", "FII", "ETF", "Renda fixa", "Cripto", "Internacional"]))
        self.form.addRow("Preço atual", self.text_field("R$ 0,00"))
        self.form.addRow("Moeda", self.combo(["BRL", "USD", "EUR"]))
        self.add_buttons("Adicionar ativo")


class AlertDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Criar alerta", "alert_dialog", parent)
        self.form.addRow("Ativo", self.text_field("Ex.: PETR4"))
        self.form.addRow("Condição", self.combo(["Preço abaixo de", "Preço acima de", "Variação percentual"]))
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
        self.form.addRow("Categoria", self.combo(["Segurança", "Patrimônio", "Experiência", "Educação", "Outro"]))
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


class PortfolioDialog(DemoFormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Nova carteira", "portfolio_dialog", parent)
        self.form.addRow("Nome", self.text_field("Nome da carteira"))
        self.form.addRow("Descrição", self.text_field("Descrição opcional"))
        self.form.addRow("Objetivo", self.combo(["Longo prazo", "Reserva", "Renda", "Objetivo específico"]))
        self.form.addRow("Perfil / Estratégia", self.combo(["Conservadora", "Moderada", "Arrojada", "Personalizada"]))
        self.add_buttons("Criar carteira")


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
