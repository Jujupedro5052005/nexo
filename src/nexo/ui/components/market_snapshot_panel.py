import json

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton

from nexo.domain.models.market_data import Quote
from nexo.ui.components.common import SectionCard
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.financial_formatting import currency_text, decimal_text


class MarketSnapshotPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Snapshot de mercado")
        self.status = QLabel("Selecione um ativo")
        self.status.setObjectName("SecondaryText")
        self.symbol = QLabel("—")
        self.symbol.setObjectName("PageTitle")
        self.name = QLabel("—")
        self.price = QLabel("—")
        self.price.setObjectName("SnapshotPrice")
        self.change = QLabel("Variação diária: —")
        for label in (self.status, self.symbol, self.name, self.price, self.change):
            label.setWordWrap(True)
            self.content.addWidget(label)
        row = QHBoxLayout()
        self.metrics = {}
        for key, title in (
            ("high", "Máxima"),
            ("low", "Mínima"),
            ("volume", "Volume"),
            ("cap", "Market Cap"),
        ):
            card = MetricCard(title, "—")
            self.metrics[key] = card
            row.addWidget(card)
        self.content.addLayout(row)
        self.details = QLabel("Selecione um resultado para consultar a cotação.")
        self.details.setObjectName("asset_quote")
        self.details.setWordWrap(True)
        self.content.addWidget(self.details)
        self.toggle = QPushButton("Ver dados técnicos")
        self.toggle.setObjectName("LinkButton")
        self.toggle.setCheckable(True)
        self.content.addWidget(self.toggle)
        self.technical = QPlainTextEdit()
        self.technical.setReadOnly(True)
        self.technical.setFixedHeight(200)
        self.technical.hide()
        self.toggle.toggled.connect(self.technical.setVisible)
        self.content.addWidget(self.technical)

    def clear(self) -> None:
        for label in (self.symbol, self.name, self.price):
            label.setText("—")
        self.status.setText("Dados indisponíveis / aguardando seleção")
        self.change.setText("Variação diária: —")
        self.technical.clear()
        self.toggle.setChecked(False)
        for card in self.metrics.values():
            card.value_label.setText("—")

    def display(self, quote: Quote) -> None:
        latency = (
            format(quote.latency_ms, ".0f") + " ms"
            if quote.latency_ms is not None
            else "—"
        )
        source = quote.source + (
            " · fechamento diário / EOD" if quote.price_kind == "eod" else ""
        )
        self.status.setText(f"Disponível · {source} · Resposta: {latency}")
        self.symbol.setText(quote.asset.symbol)
        self.name.setText(quote.name)
        self.price.setText(currency_text(quote.price, quote.currency))
        self.change.setText(
            f"Variação diária: {currency_text(quote.change, quote.currency)} · "
            + (
                decimal_text(quote.change_percent) + "%"
                if quote.change_percent is not None
                else "—"
            )
        )
        self.metrics["high"].value_label.setText(
            currency_text(quote.day_high, quote.currency)
        )
        self.metrics["low"].value_label.setText(
            currency_text(quote.day_low, quote.currency)
        )
        self.metrics["volume"].value_label.setText(
            f"{quote.volume:,}".replace(",", ".") if quote.volume is not None else "—"
        )
        self.metrics["cap"].value_label.setText(
            currency_text(quote.market_cap, quote.currency)
        )
        timestamp = (
            quote.market_time.isoformat() if quote.market_time else "não informado"
        )
        self.details.setText(
            f"{quote.asset.symbol} • {quote.name}\nPreço: {currency_text(quote.price, quote.currency)} • Moeda: {quote.currency} • Variação informada: "
            + (
                decimal_text(quote.change_percent) + "%"
                if quote.change_percent is not None
                else "—"
            )
            + "\n"
            f"Fonte: {source} • Horário do dado: {timestamp}\nConsultado: {quote.retrieved_at.isoformat(timespec='seconds')}\n"
            f"Resposta: {latency} • Dados: {quote.freshness}"
        )
        normalized = {
            "symbol": quote.asset.symbol,
            "name": quote.name,
            "currency": quote.currency,
            "current_price": quote.price,
            "daily_change": quote.change,
            "daily_change_percent": quote.change_percent,
            "day_high": quote.day_high,
            "day_low": quote.day_low,
            "open": quote.open,
            "previous_close": quote.previous_close,
            "volume": quote.volume,
            "market_cap": quote.market_cap,
            "market_timestamp": quote.market_time.isoformat()
            if quote.market_time
            else None,
            "queried_at": quote.retrieved_at.isoformat(),
            "source": quote.source,
            "latency_ms": quote.latency_ms,
            "freshness": quote.freshness,
            "data_age_seconds_at_query": quote.data_age_seconds,
            "price_kind": quote.price_kind,
            "trading_date": quote.trading_date,
        }
        self.technical.setPlainText(
            json.dumps(normalized, default=str, ensure_ascii=False, indent=2)
        )
