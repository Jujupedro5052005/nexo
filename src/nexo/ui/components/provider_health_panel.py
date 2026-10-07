from PySide6.QtWidgets import QLabel, QPushButton

from nexo.application.assets.provider_status import GetProviderHealth
from nexo.ui.components.common import SectionCard


class ProviderHealthPanel(SectionCard):
    def __init__(self, case: GetProviderHealth | None) -> None:
        super().__init__("Providers, cache e consumo local")
        self.case = case
        self.labels: list[QLabel] = []
        for _ in range(4):
            label = QLabel()
            label.setWordWrap(True)
            self.labels.append(label)
            self.content.addWidget(label)
        button = QPushButton("Atualizar diagnóstico local")
        button.setObjectName("SecondaryButton")
        button.clicked.connect(self.refresh)
        self.content.addWidget(button)
        self.refresh()

    def refresh(self) -> None:
        if self.case is None:
            self.labels[0].setText("Diagnóstico de providers não conectado.")
            return
        for label, health in zip(self.labels, self.case.execute()):
            remaining = (
                f" · X-RateLimit-Remaining: {health.quota_remaining}"
                if health.quota_remaining is not None
                else ""
            )
            label.setText(
                f"{health.provider} · {health.status} · {health.role}\n"
                f"Requests locais hoje (UTC): {health.requests_today}/{health.soft_budget} (budget local)"
                f" · cache hits: {health.cache_hits} · hit rate: {health.cache_hit_rate:.0%}{remaining}\n"
                f"Capabilities restritas: {', '.join(health.restricted_capabilities) or 'nenhuma registrada'}"
                + (
                    "\nÚltimas atualizações: " + " | ".join(health.cache_updates)
                    if health.cache_updates
                    else "\nCadastro/DFP/ITR: sem dataset em cache"
                    if health.provider == "CVM"
                    else ""
                )
            )
