from collections.abc import Callable
from pathlib import Path
from typing import Any

from nexo.application.intelligence.knowledge_service import KnowledgeService
from nexo.application.intelligence.orchestrator import IntelligenceOrchestrator
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.interfaces.intelligence import IntelligenceStorage
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    AnalysisResponse,
    ChatMessage,
    IntelligenceError,
    Methodology,
)


class IntelligenceWorkspace:
    """UI-facing application facade. Storage/network implementations are injected."""

    def __init__(
        self,
        orchestrator: IntelligenceOrchestrator,
        knowledge: KnowledgeService,
        storage: IntelligenceStorage,
        portfolios: ListPortfolios,
        import_document: Callable[[Path, bool], str],
        export_analysis: Callable[[Path, str], None],
        status: Callable[[], dict[str, Any]],
    ) -> None:
        self.orchestrator, self.knowledge, self.storage = (
            orchestrator,
            knowledge,
            storage,
        )
        self.portfolios = portfolios
        self._import, self._export, self._status = (
            import_document,
            export_analysis,
            status,
        )

    def status(self) -> dict[str, Any]:
        return self._status()

    @property
    def enabled(self) -> bool:
        return self.orchestrator.enabled

    @property
    def cloud(self) -> bool:
        return self.orchestrator.cloud

    def ask(self, request: AnalysisRequest) -> AnalysisResponse:
        return self.orchestrator.ask(request)

    def test_connection(self) -> str:
        return self.orchestrator.provider.test_connection()

    def conversations(self) -> tuple[str, ...]:
        return self.storage.conversations()

    def history(self, identity: str, limit: int = 30) -> tuple[ChatMessage, ...]:
        return self.storage.history(identity, min(limit, 30))

    def documents(self) -> list[dict[str, Any]]:
        return self.storage.documents()

    def methodologies(self) -> tuple[Methodology, ...]:
        return self.storage.methodologies()

    def delete_local_document(self, identity: str) -> None:
        doc = next(d for d in self.storage.documents() if d["id"] == identity)
        if (
            doc.get("remote_name")
            or doc.get("remote_operation")
            or doc.get("remote_submission_pending")
        ):
            raise IntelligenceError(
                "Fonte com envio remoto: use delete-document para remover o documento do File Search antes do registro local."
            )
        self.storage.delete_document(identity)

    def clear_conversations(self) -> None:
        self.storage.clear_conversations()

    def import_document(self, path: Path, authorized: bool) -> str:
        return self._import(path, authorized)

    def export(self, path: Path, response: AnalysisResponse) -> None:
        from nexo.application.intelligence.tools import encode

        self._export(
            path,
            response.markdown
            + "\n\n## Evidências\n\n```json\n"
            + encode(response)
            + "\n```\n",
        )
