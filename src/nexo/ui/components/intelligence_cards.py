"""Presentation of audited financial results. No HTTP, SQL or valuation rules."""

import json
from decimal import Decimal
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nexo.ui.components.charts import allocation_donut, line_chart
from nexo.ui.components.common import DataTable, SectionCard
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.financial_formatting import currency_text, percent_text


def money(value: Any) -> str:
    return currency_text(Decimal(str(value)) if value is not None else None)


def ratio(value: Any) -> str:
    return percent_text(Decimal(str(value)) if value is not None else None)


class EvidenceInspector(QDialog):
    def __init__(self, payload: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Detalhes técnicos · diagnóstico estruturado")
        self.resize(900, 650)
        layout = QVBoxLayout(self)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(payload)
        layout.addWidget(text)
        close = QPushButton("Fechar")
        close.clicked.connect(self.accept)
        layout.addWidget(close)


class SourceReferenceCard(SectionCard):
    def __init__(self, title: str, detail: str) -> None:
        super().__init__(title)
        label = QLabel(detail)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(label)


class MethodologyCard(SectionCard):
    def __init__(self, method: Any) -> None:
        super().__init__(method.name)
        for text in (
            f"Versão {method.version} · {method.review_status} · origem {method.origin}",
            method.description,
            "Aplicabilidade: " + ", ".join(method.applicable_asset_types),
            "Fórmula: " + method.formula_reference,
            "Entradas: " + ", ".join(method.required_inputs),
            "Limitações: " + " ".join(method.constraints),
            "Fontes: " + "; ".join(s.title for s in method.source_references),
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            self.content.addWidget(label)


class AssetAnalysisCard(SectionCard):
    selected = Signal(str)

    def __init__(self, asset: dict[str, Any]) -> None:
        super().__init__(asset["symbol"] + " · " + asset["verdict"])
        row = QHBoxLayout()
        base: dict[str, Any] = next(
            (s for s in asset.get("scenarios", []) if s["label"] == "base"), {}
        )
        for title, value in (
            ("Cotação", money(asset["quote"].get("price"))),
            ("Preço teto · base", money(base.get("ceiling_price"))),
            ("Peso na carteira", ratio(asset.get("weight"))),
            ("ROE", ratio(asset.get("fundamentals", {}).get("roe"))),
        ):
            row.addWidget(MetricCard(title, value, "Referência e premissas abaixo"))
        self.content.addLayout(row)
        position = asset.get("position") or {}
        self.content.addWidget(
            QLabel(
                "Custo médio: "
                + money(position.get("position", {}).get("average_cost"))
                + " · Retorno aberto sobre custo: "
                + ratio(position.get("unrealized_return"))
            )
        )
        risk = asset.get("risk") or {}
        if risk:
            self.content.addWidget(
                QLabel(
                    "Histórico · volatilidade anualizada: "
                    + ratio(risk.get("annual_volatility"))
                    + " · drawdown máximo: "
                    + ratio(risk.get("max_drawdown"))
                    + " · observações: "
                    + str(risk.get("observations", 0))
                )
            )
        review = QLabel("Revisar se: " + "; ".join(asset.get("review_conditions", [])))
        review.setWordWrap(True)
        review.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(review)
        explanation = QLabel(
            " ".join(asset["reasons"]) + "\n" + " · ".join(asset.get("issues", []))
        )
        explanation.setWordWrap(True)
        explanation.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(explanation)
        if asset.get("scenarios"):
            table = DataTable(
                ("CENÁRIO", "VALOR TEÓRICO", "PREÇO TETO", "ORIGEM"),
                [
                    (
                        s["label"].title(),
                        money(s.get("theoretical_value")),
                        money(s.get("ceiling_price")),
                        "Hipótese estimada · " + s["origin"],
                    )
                    for s in asset["scenarios"]
                ],
            )
            self.content.addWidget(table)
            note = QLabel(
                "Premissas: "
                + " ".join(
                    dict.fromkeys(s["justification"] for s in asset["scenarios"])
                )
            )
            note.setWordWrap(True)
            self.content.addWidget(note)
        q = asset["quote"]
        self.content.addWidget(
            QLabel(
                f"Fonte: {q.get('source', 'indisponível')} · mercado: {q.get('market_time') or 'horário não informado'}\nConsulta: {q.get('retrieved_at') or 'não informada'} · setor: {asset['sector']}"
            )
        )


class FinancialReportView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PageContent")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.report: dict[str, Any] = {}

    def clear(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

    def show_report(self, report: dict[str, Any]) -> None:
        self.clear()
        self.report = report
        if not report:
            self.content.addWidget(
                QLabel(
                    "Execute uma análise aprofundada para explorar posições, cenários e fontes."
                )
            )
            return
        headline = SectionCard("Diagnóstico da carteira")
        snapshot = report.get("snapshot") or {}
        values = snapshot.get("valuation", {})
        concentration = snapshot.get("concentration", {})
        row = QHBoxLayout()
        for title, value in (
            ("Valor aberto", money(values.get("current_market_value"))),
            ("Custo aberto", money(values.get("invested_cost"))),
            ("Top 3", ratio(concentration.get("top_three"))),
        ):
            row.addWidget(MetricCard(title, value, "Sem incluir caixa · posição atual"))
        headline.content.addLayout(row)
        if report.get("sector_exposure"):
            headline.content.addWidget(
                DataTable(
                    ("SETOR", "EXPOSIÇÃO"),
                    [(s, ratio(w)) for s, w in report["sector_exposure"].items()],
                )
            )
            headline.content.addWidget(
                allocation_donut(
                    [
                        (sector, float(weight))
                        for sector, weight in report["sector_exposure"].items()
                    ]
                )
            )
        self.content.addWidget(headline)
        for asset in report.get("assets", []):
            self.content.addWidget(AssetAnalysisCard(asset))
            points = asset.get("history", {}).get("points", [])
            if points:
                view = line_chart(
                    [
                        (
                            asset["symbol"] + " · fechamento histórico",
                            [float(p["close"]) for p in points],
                            "#10C7C7",
                        )
                    ],
                    180,
                )
                view.setToolTip(
                    f"{points[0]['timestamp']} a {points[-1]['timestamp']} · histórico do ativo, sem representar rentabilidade da carteira"
                )
                self.content.addWidget(view)
        notice = QLabel(
            report.get("macro", "") + "\n" + " · ".join(report.get("issues", []))
        )
        notice.setWordWrap(True)
        self.content.addWidget(notice)


def structured_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
