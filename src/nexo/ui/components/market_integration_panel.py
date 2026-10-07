from typing import Any

from PySide6.QtWidgets import QLabel, QPushButton

from nexo.application.assets.market_integration import (
    GetMarketIntegrationStatus,
    TestMarketConnection,
)
from nexo.domain.models.market_integration import MarketIntegrationStatus
from nexo.ui.components.common import SectionCard
from nexo.ui.workers import TaskRunner


class MarketIntegrationPanel(SectionCard):
    def __init__(
        self,
        status_case: GetMarketIntegrationStatus | None = None,
        test_connection: TestMarketConnection | None = None,
    ) -> None:
        super().__init__("Integração de mercado")
        self._test_connection = test_connection
        self.runner = TaskRunner(self)
        self._generation = 0
        self.provider_label = QLabel()
        self.configuration_label = QLabel()
        self.mode_label = QLabel()
        self.authentication_label = QLabel()
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.guidance = QLabel()
        self.guidance.setWordWrap(True)
        self.guidance.setObjectName("SecondaryText")
        self.test_button = QPushButton("Testar conexão")
        self.test_button.setObjectName("PrimaryButton")
        self.test_button.setEnabled(test_connection is not None)
        self.test_button.clicked.connect(self.test_connection)
        for widget in (
            self.provider_label,
            self.configuration_label,
            self.mode_label,
            self.authentication_label,
            self.feedback,
            self.guidance,
            self.test_button,
        ):
            self.content.addWidget(widget)
        self.status = (
            status_case.execute()
            if status_case
            else MarketIntegrationStatus(
                "brapi",
                False,
                None,
                (),
                "Diagnóstico não conectado neste contexto.",
                "unavailable",
            )
        )
        self.display(self.status)

    def display(self, status: MarketIntegrationStatus) -> None:
        self.status = status
        self.provider_label.setText(f"Provider: {status.provider}")
        self.configuration_label.setText(
            "Status: Configurado • chave configurada"
            if status.configured
            else "Status: Não configurado"
        )
        self.mode_label.setText(
            "Modo: Autenticado"
            + (
                " (a validar)"
                if status.authenticated is None
                else " • chave recusada"
                if status.authenticated is False
                else ""
            )
            if status.configured
            else "Modo: Sandbox público"
        )
        self.authentication_label.setText(
            "Autenticação: aceita para esta consulta"
            if status.authenticated is True
            else "Autenticação: chave não aceita"
            if status.authenticated is False
            else "Autenticação: não verificada"
            if status.configured
            else "Autenticação: não se aplica ao sandbox"
        )
        self.feedback.setText(status.message)
        self.guidance.setText(
            status.configuration_guidance
            + " A chave vem da configuração externa; não é exibida nem salva no banco."
        )

    def test_connection(self) -> None:
        case = self._test_connection
        if case is None:
            return
        self._generation += 1
        generation = self._generation
        self.test_button.setEnabled(False)
        self.feedback.setText("Testando conexão com brapi…")

        def completed(result: Any, error: Exception | None) -> None:
            if generation != self._generation:
                return
            self.test_button.setEnabled(True)
            if error is not None:
                self.feedback.setText(
                    "Não foi possível testar a integração. Verifique sua conexão e tente novamente."
                )
                return
            self.display(result)

        self.runner.submit(case.execute, completed)
