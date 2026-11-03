from pathlib import Path

from nexo.domain.interfaces.intelligence import (
    IntelligenceProvider,
    IntelligenceStorage,
)
from nexo.domain.models.intelligence import IntelligenceError, Methodology


class KnowledgeService:
    def __init__(
        self, storage: IntelligenceStorage, provider: IntelligenceProvider
    ) -> None:
        self.storage, self.provider = storage, provider

    def extract(self, identity: str) -> Methodology:
        doc = next(d for d in self.storage.documents() if d["id"] == identity)
        if not doc.get("authorized") or doc.get("kind") != "local":
            raise IntelligenceError("Extração exige documento local autorizado.")
        if doc.get("extracted_version") == doc.get("version"):
            raise IntelligenceError(
                "Esta versão já foi processada; importe conteúdo revisado para reprocessar."
            )
        method = self.provider.extract(str(doc["text"]))
        if method.methodology_id in {
            "gordon",
            "target_yield",
            "multiples",
            "bank_residual",
        }:
            method = method.model_copy(
                update={"methodology_id": "extracted_" + method.methodology_id}
            )
        versions = [
            m.version
            for m in self.storage.methodologies()
            if m.methodology_id == method.methodology_id
        ]
        method = method.model_copy(
            update={
                "version": max(versions, default=0) + 1,
                "review_status": "pending_review",
                "reviewed_by": None,
            }
        )
        self.storage.save_methodology(method)
        self.storage.put_document({**doc, "extracted_version": doc["version"]})
        return method

    def import_methodology(self, path: Path) -> Methodology:
        if path.stat().st_size > 100000:
            raise IntelligenceError("Metodologia JSON excede 100 KB.")
        method = Methodology.model_validate_json(path.read_text(encoding="utf-8-sig"))
        if method.methodology_id in {
            "gordon",
            "target_yield",
            "multiples",
            "bank_residual",
        }:
            raise IntelligenceError("IDs de cálculos nativos são reservados.")
        if any(
            m.methodology_id == method.methodology_id and m.version >= method.version
            for m in self.storage.methodologies()
        ):
            raise IntelligenceError(
                "A nova versão deve superar as versões já registradas."
            )
        method = method.model_copy(
            update={"review_status": "pending_review", "reviewed_by": None}
        )
        self.storage.save_methodology(method)
        return method

    def review(
        self, identity: str, version: int, *, approve: bool, reviewer: str
    ) -> Methodology:
        if not reviewer.strip():
            raise IntelligenceError("Identifique o revisor.")
        method = next(
            m
            for m in self.storage.methodologies()
            if m.methodology_id == identity and m.version == version
        )
        if method.review_status not in {"draft", "pending_review"}:
            raise IntelligenceError("A metodologia não está pendente de revisão.")
        result = method.model_copy(
            update={
                "review_status": "approved" if approve else "rejected",
                "reviewed_by": reviewer.strip(),
            }
        )
        if approve:
            for previous in self.storage.methodologies():
                if (
                    previous.methodology_id == identity
                    and previous.review_status == "approved"
                ):
                    self.storage.save_methodology(
                        previous.model_copy(update={"review_status": "superseded"})
                    )
        self.storage.save_methodology(result)
        return result
