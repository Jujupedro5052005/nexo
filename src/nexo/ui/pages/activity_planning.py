from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nexo.ui.components.charts import bar_chart, donut_chart
from nexo.ui.components.common import Badge, DataTable, PageContent, SectionCard
from nexo.ui.components.metric_card import MetricCard
from nexo.ui.demo.data import DEMO_NOTICE, TRANSACTIONS
from nexo.ui.icons import icon


class TransactionsPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("transactions")
        top = QHBoxLayout()
        top.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        top.addStretch()
        create = QPushButton("+  Nova movimentação")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(lambda: self.dialog_requested.emit("transaction"))
        top.addWidget(create)
        self.page_layout.addLayout(top)

        filters = SectionCard("Filtros")
        fields = QHBoxLayout()
        for items in (
            ["Todas as carteiras", "Longo Prazo", "Reserva", "Internacional"],
            ["Todos os tipos", "Compra", "Venda", "Aporte", "Retirada", "Provento"],
            ["Todos os ativos", "PETR4", "VALE3", "ITUB4", "IVVB11"],
            ["Este mês", "3 meses", "6 meses", "1 ano", "Máximo"],
        ):
            combo = QComboBox()
            combo.addItems(items)
            fields.addWidget(combo)
        search = QLineEdit()
        search.setPlaceholderText("Buscar movimentação")
        fields.addWidget(search, 1)
        filters.content.addLayout(fields)
        self.page_layout.addWidget(filters)

        card = SectionCard("Histórico de movimentações")
        rows = [row + ("Ver  Editar  Excluir",) for row in TRANSACTIONS]
        table = DataTable(
            ("DATA", "CARTEIRA", "TIPO", "ATIVO", "QUANTIDADE", "PREÇO", "VALOR TOTAL", "AÇÕES"),
            rows,
        )
        table.setObjectName("transactions_table")
        for row in range(table.rowCount()):
            actions = QWidget()
            action_layout = QHBoxLayout(actions)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(2)
            for label in ("Ver", "Editar", "Excluir"):
                button = QPushButton(label)
                button.setObjectName("LinkButton")
                button.clicked.connect(
                    lambda _checked=False: self.dialog_requested.emit("transaction")
                )
                action_layout.addWidget(button)
            table.setCellWidget(row, 7, actions)
        table.cellDoubleClicked.connect(
            lambda *_: self.dialog_requested.emit("transaction")
        )
        card.content.addWidget(table)
        self.page_layout.addWidget(card)
        self.page_layout.addStretch()


class PlanningPage(PageContent):
    dialog_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("planning")
        row = QHBoxLayout()
        row.addWidget(Badge(DEMO_NOTICE, "DemoBadge"))
        row.addStretch()
        for label in ("+  Receita", "+  Despesa"):
            button = QPushButton(label)
            button.setObjectName("PrimaryButton" if "Receita" in label else "SecondaryButton")
            button.clicked.connect(lambda: self.dialog_requested.emit("notice"))
            row.addWidget(button)
        self.page_layout.addLayout(row)

        metrics = QHBoxLayout()
        for label, value, detail, name in (
            ("RECEITA MENSAL", "R$ 12.300", "Média demonstrativa", "cashflow"),
            ("DESPESAS FIXAS", "R$ 5.120", "41,6% da receita", "planning"),
            ("DESPESAS VARIÁVEIS", "R$ 2.380", "19,3% da receita", "wallet"),
            ("CAPACIDADE DE APORTE", "R$ 4.800", "39,1% disponível", "target"),
        ):
            metrics.addWidget(MetricCard(label, value, detail, icon(name, "#10C7C7")), 1)
        self.page_layout.addLayout(metrics)

        chart_row = QGridLayout()
        chart_row.setSpacing(14)
        comparison = SectionCard("Receita x Despesa")
        comparison.content.addWidget(
            bar_chart(
                ["Abr", "Mai", "Jun", "Jul", "Ago", "Set"],
                (("Receita", [11.5, 12, 12, 12.4, 12.1, 12.3], "#3DDC84"), ("Despesa", [7.2, 7.6, 7.1, 7.9, 7.4, 7.5], "#FF5C6C")),
            )
        )
        distribution = SectionCard("Distribuição mensal")
        categories = [
            ("Moradia", 31, "R$ 2.325", "#4D7CFF"),
            ("Alimentação", 19, "R$ 1.425", "#10C7C7"),
            ("Transporte", 14, "R$ 1.050", "#8B6CFF"),
            ("Lazer", 12, "R$ 900", "#FFB020"),
            ("Educação", 9, "R$ 675", "#3DDC84"),
            ("Saúde", 8, "R$ 600", "#FF5C6C"),
            ("Outros", 7, "R$ 525", "#6E7D91"),
        ]
        distribution.content.addWidget(donut_chart(categories))
        chart_row.addWidget(comparison, 0, 0, 1, 2)
        chart_row.addWidget(distribution, 0, 2)
        chart_row.setColumnStretch(0, 2)
        chart_row.setColumnStretch(1, 2)
        chart_row.setColumnStretch(2, 2)
        self.page_layout.addLayout(chart_row)

        details = QGridLayout()
        details.setSpacing(14)
        for column, (title, items) in enumerate((
            ("Receitas", (("Salário", "R$ 10.500"), ("Outras receitas", "R$ 1.800"))),
            ("Despesas fixas", (("Moradia", "R$ 2.900"), ("Educação", "R$ 1.100"), ("Serviços", "R$ 1.120"))),
            ("Despesas variáveis", (("Alimentação", "R$ 980"), ("Lazer", "R$ 720"), ("Outros", "R$ 680"))),
        )):
            card = SectionCard(title)
            for label, value in items:
                line = QHBoxLayout()
                line.addWidget(QLabel(label))
                line.addStretch()
                line.addWidget(QLabel(value))
                card.content.addLayout(line)
            details.addWidget(card, 0, column)
        self.page_layout.addLayout(details)

        capacity = SectionCard("Capacidade de investimento")
        info = QHBoxLayout()
        for label, value in (("Renda líquida", "R$ 12.300"), ("Despesas", "R$ 7.500"), ("Reserva", "R$ 1.200"), ("Aporte sugerido", "R$ 3.600")):
            block = QVBoxLayout()
            caption = QLabel(label)
            caption.setObjectName("SecondaryText")
            amount = QLabel(value)
            amount.setObjectName("AccentText" if label == "Aporte sugerido" else "SectionTitle")
            block.addWidget(caption)
            block.addWidget(amount)
            info.addLayout(block)
        capacity.content.addLayout(info)
        disclaimer = QLabel("Simulação visual; não representa recomendação financeira.")
        disclaimer.setObjectName("SecondaryText")
        capacity.content.addWidget(disclaimer)
        self.page_layout.addWidget(capacity)
