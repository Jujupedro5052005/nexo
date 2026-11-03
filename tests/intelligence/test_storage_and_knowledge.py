from concurrent.futures import ThreadPoolExecutor

import pytest

from nexo.domain.models.intelligence import IntelligenceError, QuotaExceeded
from nexo.infrastructure.intelligence.knowledge import LocalKnowledgeRetriever
from nexo.infrastructure.intelligence.storage import SqliteIntelligenceStorage


def test_quota_atomic_across_connections_and_reopen(storage):
    def reserve(_):
        try:
            return storage.reserve("test", 10, 3, 100)
        except QuotaExceeded:
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(reserve, range(10)))
    assert sum(v is not None for v in results) == 3
    reopened = SqliteIntelligenceStorage(storage.path)
    assert reopened.usage()["requests"] == 3
    assert reopened.usage()["tokens_accounted"] == 30
    with pytest.raises(QuotaExceeded):
        reopened.reserve("test", 1, 3, 100)


def test_token_reservation_settlement_failure_and_cache(storage):
    identity = storage.reserve("test", 90, 10, 100)
    with pytest.raises(QuotaExceeded):
        storage.reserve("test", 11, 10, 100)
    storage.finish_usage(identity, 5, "complete")
    storage.reserve("test", 90, 10, 100)
    assert storage.usage()["tokens_accounted"] == 95
    storage.cache("context", "answer")
    assert storage.cached("context") == "answer"
    assert storage.cached("different") is None
    storage.save_turn("a", "Q", "A")
    storage.clear_conversations()
    assert storage.cached("context") is None
    assert storage.history("a") == ()
    assert storage.usage()["requests"] == 2


def test_documents_dedup_authorization_and_local_retrieval(storage, tmp_path):
    path = tmp_path / "manual.md"
    path.write_text(
        "Gordon exige Ke maior que crescimento. Dividendos futuros são premissas.",
        encoding="utf-8",
    )
    local = LocalKnowledgeRetriever(storage)
    with pytest.raises(IntelligenceError):
        local.import_document(path, authorized=False)
    identity = local.import_document(path, authorized=True)
    assert local.import_document(path, authorized=True) == identity
    assert len(storage.documents()) == 1
    hits = local.search("Gordon crescimento")
    assert hits[0].document_id == identity
    assert hits[0].sources[0].uri.startswith("nexo://")
    assert local.search("inexistente") == ()
    path.write_text("Gordon versão atualizada", encoding="utf-8")
    assert local.import_document(path, authorized=True) != identity
    storage.delete_document(identity)
    assert len(storage.documents()) == 1


def test_extraction_forces_review_and_versions(workspace, storage, tmp_path):
    path = tmp_path / "manual.md"
    path.write_text("dividendos sintéticos", encoding="utf-8")
    identity = workspace.import_document(path, True)
    method = storage.methodologies()[0]
    workspace.knowledge.provider.extract = lambda text: method.model_copy(
        update={"review_status": "approved"}
    )
    extracted = workspace.knowledge.extract(identity)
    assert extracted.methodology_id.startswith("extracted_")
    assert extracted.review_status == "pending_review"
    assert extracted.reviewed_by is None
    with pytest.raises(IntelligenceError, match="já foi processada"):
        workspace.knowledge.extract(identity)
    approved = workspace.knowledge.review(
        extracted.methodology_id, 1, approve=True, reviewer="Pessoa revisora"
    )
    assert approved.review_status == "approved"
    with pytest.raises(IntelligenceError):
        workspace.knowledge.review(
            extracted.methodology_id, 1, approve=True, reviewer=""
        )
    storage.save_methodology(extracted.model_copy(update={"version": 2}))
    workspace.knowledge.review(
        extracted.methodology_id, 2, approve=True, reviewer="Revisor"
    )
    assert (
        next(
            m
            for m in storage.methodologies()
            if m.methodology_id == extracted.methodology_id and m.version == 1
        ).review_status
        == "superseded"
    )


def test_imported_json_cannot_approve_itself_or_override_builtins(
    workspace, storage, tmp_path
):
    method = storage.methodologies()[0]
    path = tmp_path / "method.json"
    path.write_text(method.model_dump_json(), encoding="utf-8")
    with pytest.raises(IntelligenceError, match="reservados"):
        workspace.knowledge.import_methodology(path)
    path.write_text(
        method.model_copy(
            update={"methodology_id": "external_method"}
        ).model_dump_json(),
        encoding="utf-8",
    )
    imported = workspace.knowledge.import_methodology(path)
    assert imported.review_status == "pending_review"
    with pytest.raises(IntelligenceError, match="versão"):
        workspace.knowledge.import_methodology(path)
