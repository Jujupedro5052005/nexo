from datetime import datetime

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from nexo.application.portfolio.financial_summary import transaction_amounts
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.asset import Asset
from nexo.domain.models.transaction import Transaction
from nexo.ui.decimal_parser import DecimalInputError, parse_decimal
from nexo.ui.financial_formatting import decimal_text, money_text


class TransactionDialog(QDialog):
    """Collect input and accept only after the application commits the ledger entry."""

    transaction_created = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        register_transaction: RegisterTransaction | None = None,
        portfolio_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self._register_transaction = register_transaction
        self._portfolio_id = portfolio_id
        self.setObjectName("transaction_dialog")
        self.setWindowTitle("Nova movimentação")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        heading = QLabel("Nova movimentação")
        heading.setObjectName("DialogTitle")
        layout.addWidget(heading)
        form = QFormLayout()
        self.portfolio_label = QLabel(
            f"Carteira #{portfolio_id}"
            if portfolio_id
            else "Nenhuma carteira selecionada"
        )
        form.addRow("Carteira selecionada", self.portfolio_label)
        self.transaction_type = QComboBox()
        self.transaction_type.addItem("Compra (BUY)", TransactionType.BUY)
        self.transaction_type.addItem("Venda (SELL)", TransactionType.SELL)
        form.addRow("Tipo", self.transaction_type)
        self.asset_symbol = QLineEdit()
        self.asset_symbol.setPlaceholderText("Ex.: PETR4")
        self.asset_symbol.setObjectName("transaction_asset")
        form.addRow("Ativo", self.asset_symbol)
        self.quantity = QLineEdit()
        self.unit_price = QLineEdit()
        self.fees = QLineEdit("0")
        for label, field, name in (
            ("Quantidade", self.quantity, "transaction_quantity"),
            ("Preço unitário", self.unit_price, "transaction_price"),
            ("Taxas", self.fees, "transaction_fees"),
        ):
            field.setObjectName(name)
            field.setPlaceholderText("Ex.: 10,50")
            field.textChanged.connect(self.update_summary)
            form.addRow(label, field)
        self.occurred_at = QDateTimeEdit(QDateTime.currentDateTime())
        self.occurred_at.setCalendarPopup(True)
        self.occurred_at.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.occurred_at.setObjectName("transaction_datetime")
        form.addRow("Data e hora", self.occurred_at)
        layout.addLayout(form)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.feedback = QLabel()
        self.feedback.setObjectName("WarningBadge")
        self.feedback.setWordWrap(True)
        self.feedback.hide()
        layout.addWidget(self.feedback)
        buttons = QDialogButtonBox()
        cancel = buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        cancel.setObjectName("SecondaryButton")
        self.save_button = buttons.addButton(
            "Salvar movimentação", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.save_button.setObjectName("PrimaryButton")
        buttons.rejected.connect(self.reject)
        self.save_button.clicked.connect(self._save)
        layout.addWidget(buttons)
        self.transaction_type.currentIndexChanged.connect(self.update_summary)
        self.asset_symbol.textChanged.connect(self.update_summary)
        self.update_summary()
        if portfolio_id is None or register_transaction is None:
            self.feedback.setText(
                "Selecione uma carteira na página Carteiras antes de registrar movimentações."
            )
            self.feedback.show()
            self.save_button.setEnabled(False)

    def _transaction(self) -> Transaction:
        if self._portfolio_id is None:
            raise DecimalInputError("Selecione uma carteira.")
        numbers = {}
        for name, label, field in (
            ("quantity", "Quantidade", self.quantity),
            ("unit_price", "Preço unitário", self.unit_price),
            ("fees", "Taxas", self.fees),
        ):
            try:
                numbers[name] = parse_decimal(field.text(), allow_zero=name == "fees")
            except DecimalInputError as error:
                raise DecimalInputError(f"{label}: {error}") from error
        if not self.asset_symbol.text().strip():
            raise DecimalInputError("Informe o símbolo do ativo.")
        date = self.occurred_at.dateTime()
        # The form captures a wall-clock datetime, without attaching a timezone.
        occurred_at = datetime.fromisoformat(date.toString("yyyy-MM-ddTHH:mm:ss"))
        return Transaction(
            portfolio_id=self._portfolio_id,
            asset=Asset(self.asset_symbol.text()),
            transaction_type=self.transaction_type.currentData(),
            occurred_at=occurred_at,
            quantity=numbers["quantity"],
            unit_price=numbers["unit_price"],
            fees=numbers["fees"],
        )

    def update_summary(self) -> None:
        if not hasattr(self, "summary"):
            return
        try:
            item = self._transaction()
            gross, settlement = transaction_amounts(item)
        except (DecimalInputError, DomainValidationError):
            self.summary.setText(
                "Preencha os dados para conferir o total da movimentação."
            )
            return
        label = (
            "Custo da compra"
            if item.transaction_type is TransactionType.BUY
            else "Receita líquida"
        )
        self.summary.setText(
            f"Valor bruto: {money_text(gross)} • {label}: {money_text(settlement)}"
        )

    def _save(self) -> None:
        if self._register_transaction is None:
            return
        self.save_button.setEnabled(False)
        try:
            saved = self._register_transaction.execute(self._transaction())
        except InsufficientPositionError as error:
            self.feedback.setText(
                f"Na data desta operação, você possui {decimal_text(error.available)} "
                f"{error.symbol} nesta carteira. Não é possível vender {decimal_text(error.requested)}."
            )
            self.feedback.show()
        except DecimalInputError as error:
            self.feedback.setText(str(error))
            self.feedback.show()
        except DomainValidationError:
            self.feedback.setText(
                "A movimentação tornaria o histórico inválido. Confira os dados e a data. Não misture datas com e sem fuso horário."
            )
            self.feedback.show()
        except TransactionRepositoryError:
            self.feedback.setText(
                "Não foi possível salvar a movimentação. Verifique a carteira e tente novamente."
            )
            self.feedback.show()
        else:
            self.transaction_created.emit(saved)
            self.accept()
        finally:
            self.save_button.setEnabled(True)
