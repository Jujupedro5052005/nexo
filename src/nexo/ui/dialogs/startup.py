from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from nexo.ui.components.common import Badge, SectionCard, action_button
from nexo.ui.components.companion import CompanionCard, CompanionState


class StartupDialog(QDialog):
    """Choose the data environment before composing repositories or providers."""

    def __init__(self) -> None:
        super().__init__()
        self.demo: bool | None = None
        self.setWindowTitle("Bem-vindo ao Nexo")
        self.setObjectName("PageContent")
        self.resize(740, 440)
        self.setMinimumWidth(620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("NEXO  /  Invista com clareza")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        companion = CompanionCard(
            "Bem-vindo. Escolha como explorar o Nexo nesta sessão."
        )
        companion.help_button.setText("Sobre os modos")
        companion.help_requested.connect(
            lambda: companion.set_state(
                CompanionState.EXPLAINING,
                "Demo usa exemplos em banco separado. Normal mantém seus registros. Fechar esta tela cancela a abertura sem criar dados.",
            )
        )
        layout.addWidget(companion)
        row = QHBoxLayout()
        self.demo_button = action_button("Explorar demonstração", True)
        self.normal_button = action_button("Abrir meu ambiente")
        for name, detail, button, value in (
            (
                "Modo Demo",
                "Carteiras e exemplos fictícios prontos. Alterações ficam no ambiente de demonstração.",
                self.demo_button,
                True,
            ),
            (
                "Modo Normal",
                "Seus dados locais. No primeiro acesso, crie uma carteira para começar. Dados anteriores são preservados.",
                self.normal_button,
                False,
            ),
        ):
            card = SectionCard(name)
            text = QLabel(detail)
            text.setWordWrap(True)
            card.content.addWidget(text)
            card.content.addWidget(button)
            button.clicked.connect(
                lambda _checked=False, selected=value: self.choose(selected)
            )
            row.addWidget(card, 1)
        layout.addLayout(row)
        layout.addWidget(Badge("Ambientes separados · nenhuma ordem real é executada"))

    def choose(self, demo: bool) -> None:
        self.demo = demo
        self.accept()


def choose_startup_mode() -> bool | None:
    dialog = StartupDialog()
    return dialog.demo if dialog.exec() == QDialog.DialogCode.Accepted else None
