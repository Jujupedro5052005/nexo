from datetime import datetime
from decimal import Decimal
from typing import Any

from PySide6.QtCore import QDateTime, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nexo.application.assets.market_data import GetAssetQuote
from nexo.application.portfolio.financial_summary import transaction_amounts
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.calculations.valuation.trade import (
    preview_trade,
    quantity_for_total,
    trade_total,
)
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError, InsufficientPositionError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.domain.models.position import Position
from nexo.domain.models.transaction import Transaction
from nexo.domain.services.cash_ledger import InsufficientCashError
from nexo.ui.decimal_parser import DecimalInputError, parse_decimal
from nexo.ui.financial_formatting import decimal_text, money_text
from nexo.ui.workers import TaskRunner


class TransactionDialog(QDialog):
    """Collect input and accept only after the application commits the ledger entry."""

    transaction_created = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        register_transaction: RegisterTransaction | None = None,
        portfolio_id: int | None = None,
        positions: tuple[Position, ...] = (),
        get_quote: GetAssetQuote | None = None,
    ) -> None:
        super().__init__(parent)
        self._register_transaction = register_transaction
        self._portfolio_id = portfolio_id
        self._positions = {position.asset.symbol: position for position in positions}
        self._get_quote = get_quote
        self.runner = TaskRunner(parent if parent is not None else self)
        self._quote_generation = 0
        self._sizing_by_total = False
        self._syncing = False
        self.quote_timer = QTimer(self)
        self.quote_timer.setSingleShot(True)
        self.quote_timer.setInterval(500)
        self.quote_timer.timeout.connect(self.load_reference)
        self.finished.connect(self.quote_timer.stop)
        self.finished.connect(lambda: self.runner.stop())
        self.setObjectName("transaction_dialog")
        self.setWindowTitle("Boleta de simulação • compra e venda")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        heading = QLabel("Boleta de simulação")
        heading.setObjectName("DialogTitle")
        layout.addWidget(heading)
        intro = QLabel(
            "1. Escolha compra ou venda e o ativo.  2. Confira preço e quantidade.  3. Revise e registre no histórico local."
        )
        intro.setWordWrap(True)
        intro.setObjectName("SecondaryText")
        layout.addWidget(intro)
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
        completer = QCompleter(sorted(self._positions), self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.asset_symbol.setCompleter(completer)
        form.addRow("Ativo", self.asset_symbol)
        self.position_label = QLabel("Digite um ativo ou escolha uma posição abaixo.")
        self.position_label.setWordWrap(True)
        self.position_label.setToolTip(
            "Saldo atual reconstruído do ledger. Para datas retroativas, a validação definitiva considera todo o histórico ao salvar."
        )
        form.addRow("Sua posição atual  ?", self.position_label)
        shortcuts = QHBoxLayout()
        self.position_picker = QComboBox()
        self.position_picker.addItem("Escolher ativo da carteira", "")
        for symbol in sorted(self._positions):
            self.position_picker.addItem(symbol, symbol)
        self.position_picker.currentIndexChanged.connect(
            lambda: self.asset_symbol.setText(self.position_picker.currentData())
        )
        shortcuts.addWidget(self.position_picker)
        self.quote_button = QPushButton("Atualizar cotação")
        self.quote_button.setObjectName("SecondaryButton")
        self.quote_button.setEnabled(get_quote is not None)
        self.quote_button.clicked.connect(lambda: self.load_reference(refresh=True))
        shortcuts.addWidget(self.quote_button)
        form.addRow("Preenchimento assistido", shortcuts)
        self.quantity = QLineEdit()
        self.unit_price = QLineEdit()
        self.total_amount = QLineEdit()
        self.manual_price = QCheckBox("Informar preço manualmente")
        self.manual_price.setChecked(get_quote is None)
        self.manual_price.toggled.connect(self.price_mode_changed)
        self.unit_price.setReadOnly(get_quote is not None)
        form.addRow("Modo de preço", self.manual_price)
        self.reference_label = QLabel(
            "Informe um ativo para consultar a cotação. Nenhuma ordem é enviada a corretoras."
        )
        self.reference_label.setWordWrap(True)
        self.fees = QLineEdit("0", self)
        self.fees.setObjectName("transaction_fees")
        self.fees.textChanged.connect(self.update_summary)
        for label, field, name in (
            ("Quantidade", self.quantity, "transaction_quantity"),
            ("Preço unitário", self.unit_price, "transaction_price"),
            ("Valor total (R$)", self.total_amount, "transaction_total"),
        ):
            field.setObjectName(name)
            field.setPlaceholderText("Ex.: 10,50")
            field.textChanged.connect(self.update_summary)
            form.addRow(label, field)
        self.fees.hide()
        form.addRow("Taxas padrão", QLabel("R$ 0,00"))
        self.total_amount.setToolTip(
            "Valor bruto desejado. Quantidade simulada com até 8 casas decimais, arredondada para baixo; confira o valor efetivo na prévia."
        )
        self.quantity.textChanged.connect(self.quantity_changed)
        self.total_amount.textChanged.connect(self.total_changed)
        self.unit_price.textChanged.connect(self.price_changed)
        quantity_shortcuts = QHBoxLayout()
        for label, fraction in (
            ("25% da posição", Decimal("0.25")),
            ("50% da posição", Decimal("0.5")),
            ("100% da posição", Decimal(1)),
        ):
            button = QPushButton(label)
            button.setObjectName("SecondaryButton")
            button.clicked.connect(
                lambda _checked=False, part=fraction: self.use_position(part)
            )
            quantity_shortcuts.addWidget(button)
        form.addRow("Quantidade assistida", quantity_shortcuts)
        form.addRow("Referência de preço", self.reference_label)
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
        self.asset_symbol.textChanged.connect(self.asset_changed)
        self.update_summary()
        if portfolio_id is None or register_transaction is None:
            self.feedback.setText(
                "Selecione uma carteira na página Carteiras antes de registrar movimentações."
            )
            self.feedback.show()
            self.save_button.setEnabled(False)

    def asset_changed(self) -> None:
        self.quote_timer.stop()
        self.runner.cancel()
        self._quote_generation += 1
        self.reference_label.setText(
            "Preço manual • informe o preço para o novo ativo."
            if self.manual_price.isChecked()
            else "Aguardando cotação automática do ativo…"
        )
        self.unit_price.clear()
        self.quote_button.setEnabled(self._get_quote is not None)
        if (
            self._get_quote is not None
            and not self.manual_price.isChecked()
            and self.asset_symbol.text().strip()
        ):
            self.quote_timer.start()
        self.update_summary()

    def price_mode_changed(self, manual: bool) -> None:
        self.quote_timer.stop()
        self.runner.cancel()
        self._quote_generation += 1
        self.unit_price.setReadOnly(not manual)
        self.quote_button.setEnabled(self._get_quote is not None)
        if manual:
            self.reference_label.setText(
                "Preço manual. Confira o valor antes de registrar."
            )
        else:
            self.unit_price.clear()
            self.load_reference()

    def quantity_changed(self) -> None:
        if not self._syncing:
            self._sizing_by_total = False
            self.sync_amounts()

    def total_changed(self) -> None:
        if not self._syncing:
            self._sizing_by_total = True
            self.sync_amounts()

    def price_changed(self) -> None:
        self.sync_amounts()

    def sync_amounts(self) -> None:
        if self._syncing:
            return
        self._syncing = True
        target = self.quantity if self._sizing_by_total else self.total_amount
        try:
            price = parse_decimal(self.unit_price.text())
            source = self.total_amount if self._sizing_by_total else self.quantity
            value = parse_decimal(source.text())
            result = (
                quantity_for_total(value, price)
                if self._sizing_by_total
                else trade_total(value, price)
            )
            target.setText(decimal_text(result))
        except (DecimalInputError, ValueError):
            target.clear()
        finally:
            self._syncing = False
        self.update_summary()

    def use_position(self, fraction: Decimal) -> None:
        position = self._positions.get(self.asset_symbol.text().strip().upper())
        if position:
            self.quantity.setText(decimal_text(position.quantity * fraction))

    def load_reference(self, *, refresh: bool = False) -> None:
        if self._get_quote is None:
            return
        if self.manual_price.isChecked():
            self.manual_price.blockSignals(True)
            self.manual_price.setChecked(False)
            self.manual_price.blockSignals(False)
            self.unit_price.setReadOnly(True)
            self.unit_price.clear()
        self.quote_timer.stop()
        self.runner.cancel()
        try:
            asset = Asset(self.asset_symbol.text())
        except DomainValidationError:
            self.reference_label.setText("Informe primeiro um ticker válido.")
            return
        self._quote_generation += 1
        generation = self._quote_generation
        original_price = self.unit_price.text()
        self.quote_button.setEnabled(False)
        self.reference_label.setText("Consultando preço de referência…")
        case = self._get_quote

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._quote_generation:
                return
            self.quote_button.setEnabled(True)
            if (
                error
                or not isinstance(result, Quote)
                or result.currency != "BRL"
                or result.asset != asset
            ):
                self.reference_label.setText(
                    "Cotação BRL indisponível. Marque Informar preço manualmente para continuar."
                )
                return
            if (
                self.unit_price.text() == original_price
                and not self.manual_price.isChecked()
            ):
                self.unit_price.setText(decimal_text(result.price))
            self.reference_label.setText(
                f"{result.source} • {result.market_time or 'horário de mercado não informado'} • {result.freshness}. Para editar, use o modo manual."
            )

        self.runner.submit(
            lambda: case.execute(asset, explicit=True, refresh=refresh), completed
        )

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
        symbol = self.asset_symbol.text().strip().upper()
        position = self._positions.get(symbol)
        self.position_label.setText(
            f"{symbol} • {decimal_text(position.quantity)} unidades • preço médio {money_text(position.average_cost)}"
            if position
            else "Sem posição atual neste ativo."
        )
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
        preview = preview_trade(item, position)
        self.summary.setText(
            f"Valor bruto: {money_text(gross)} • Taxas: {money_text(item.fees)} • {label}: {money_text(settlement)}\n"
            f"Saldo após simulação: {decimal_text(preview.remaining)} • Novo preço médio: {money_text(preview.average_cost) if preview.average_cost is not None else '—'}"
            + (
                f"\nResultado estimado desta venda: {money_text(preview.realized)}"
                if preview.realized is not None
                else ""
            )
            + (
                "\nQuantidade superior à posição atual. Confira a quantidade e a data."
                if preview.remaining < 0
                else ""
            )
            + "\nPrévia usa a posição atual; operações retroativas são recalculadas pelo histórico ao salvar."
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
        except InsufficientCashError as error:
            self.feedback.setText(str(error))
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
