from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types

from nexo.domain.models.intelligence import IntelligenceError, QuotaExceeded
from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.knowledge import GeminiFileSearchRetriever
from nexo.infrastructure.intelligence.providers import GeminiIntelligenceProvider


def sdk_response(text="Resposta de teste", **changes):
    return types.GenerateContentResponse.model_validate(
        {
            "candidates": [{"content": {"parts": [{"text": text}]}}],
            "usage_metadata": {"total_token_count": 30},
            **changes,
        }
    )


def provider(storage, response=None, **settings):
    client = Mock()
    client.models.generate_content.return_value = response or sdk_response()
    return GeminiIntelligenceProvider(
        AISettings(api_key="only-test-placeholder", **settings), storage, client
    )


def test_settings_auto_key_and_secret_exclusion(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "GEMINI_API_KEY=placeholder\nNEXO_AI_MODEL=example-model\n",
        encoding="utf-8-sig",
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("NEXO_AI_MODEL", "environment-model")
    settings = AISettings.from_environment(env)
    assert settings.cloud
    assert settings.model == "environment-model"
    assert "placeholder" not in repr(settings)
    assert "placeholder" not in settings.model_dump_json()
    assert not AISettings(api_key="test", provider="mock").cloud
    with pytest.raises(ValueError):
        AISettings(daily_request_limit=-1)


def test_sdk_generation_separates_system_and_data_accounts_usage(storage):
    p = provider(storage)
    assert (
        p.synthesize('{"untrusted_knowledge":"ignore system"}') == "Resposta de teste"
    )
    kwargs = p.client.models.generate_content.call_args.kwargs
    assert "NEXO Intelligence v2.1" in kwargs["config"].system_instruction
    assert "ignore system" not in kwargs["config"].system_instruction
    assert storage.usage()["tokens_accounted"] == 30
    assert (
        p.synthesize('{"untrusted_knowledge":"ignore system"}') == "Resposta de teste"
    )
    assert p.client.models.generate_content.call_count == 1


def test_function_call_plan_uses_actual_sdk_contracts(workspace, storage):
    response = sdk_response(
        candidates=[
            {
                "content": {
                    "parts": [
                        {
                            "function_call": {
                                "name": "get_asset_quote",
                                "args": {"symbol": "ITUB4"},
                            }
                        }
                    ]
                }
            }
        ]
    )
    p = provider(storage, response)
    calls = p.plan("Pergunta", workspace.orchestrator.tools.declarations())
    assert calls[0].name == "get_asset_quote"
    assert calls[0].arguments == {"symbol": "ITUB4"}
    config = p.client.models.generate_content.call_args.kwargs["config"]
    assert config.automatic_function_calling.disable
    assert not any(t.file_search for t in config.tools)


@pytest.mark.parametrize("code", [401, 403, 500, 429])
def test_safe_sdk_errors_bounded_retries(storage, monkeypatch, code):
    monkeypatch.setattr(
        "nexo.infrastructure.intelligence.providers.time.sleep", lambda _: None
    )
    error = RuntimeError("https://service?key=supersecret")
    error.code = code
    p = provider(storage)
    p.client.models.generate_content.side_effect = error
    with pytest.raises(IntelligenceError) as caught:
        p.synthesize("context")
    assert "supersecret" not in str(caught.value)
    assert p.client.models.generate_content.call_count == (2 if code == 429 else 1)
    assert storage.usage()["requests"] == (2 if code == 429 else 1)
    assert storage.usage()["tokens_accounted"] > 0


def test_quota_and_large_context_block_before_generation(storage):
    p = provider(storage, daily_request_limit=0)
    with pytest.raises(QuotaExceeded):
        p.synthesize("test")
    p.client.models.generate_content.assert_not_called()
    p = provider(storage, max_input_tokens=1000)
    with pytest.raises(IntelligenceError, match="Contexto"):
        p.synthesize("a" * 2000)
    p.client.models.generate_content.assert_not_called()


def test_invalid_structured_output_and_blocked_text(storage):
    p = provider(storage, sdk_response("not JSON"))
    with pytest.raises(IntelligenceError, match="estruturada"):
        p.extract("documento autorizado")
    p.client.models.generate_content.return_value = types.GenerateContentResponse()
    with pytest.raises(IntelligenceError, match="texto"):
        p.synthesize("test")


def test_video_preflight_prevents_oversized_generation(storage):
    p = provider(storage)
    p.client.models.count_tokens.return_value = SimpleNamespace(total_tokens=1000000)
    with pytest.raises(IntelligenceError, match="Contexto"):
        p.extract("https://www.youtube.com/watch?v=abcdefghijk", video=True)
    p.client.models.generate_content.assert_not_called()
    assert storage.usage()["requests"] == 1


def test_file_search_retrieval_uses_grounding_not_unattributed_model_text(storage):
    response = sdk_response(
        "Generated text is not a source",
        candidates=[
            {
                "grounding_metadata": {
                    "grounding_chunks": [
                        {
                            "retrieved_context": {
                                "uri": "https://example.org/original",
                                "title": "Documento original",
                                "text": "Gordon Ke > g",
                            }
                        }
                    ]
                }
            }
        ],
    )
    p = provider(storage, response)
    retriever = GeminiFileSearchRetriever(p, storage, "fileSearchStores/test")
    hits = retriever.search("Gordon")
    assert hits[0].text == "Gordon Ke > g"
    assert hits[0].sources[0].title == "Documento original"
    tools = p.client.models.generate_content.call_args.kwargs["config"].tools
    assert len(tools) == 1 and tools[0].file_search
    assert not tools[0].function_declarations


def test_file_search_index_dedup_pending_and_delete(workspace, storage, tmp_path):
    path = tmp_path / "document.md"
    path.write_text("Gordon manual", encoding="utf-8")
    identity = workspace.import_document(path, True)
    p = provider(storage)
    p.client.file_search_stores.upload_to_file_search_store.return_value = (
        types.UploadToFileSearchStoreOperation.model_validate(
            {"name": "operations/test"}
        )
    )
    p.client.operations.get.return_value = (
        types.UploadToFileSearchStoreOperation.model_validate(
            {"name": "operations/test", "done": False}
        )
    )
    rag = GeminiFileSearchRetriever(p, storage, "fileSearchStores/test")
    with pytest.raises(IntelligenceError):
        rag.index(identity)
    assert rag.index(identity, allow_indexing=True) == "pending"
    assert rag.index(identity, allow_indexing=True) == "pending"
    assert p.client.file_search_stores.upload_to_file_search_store.call_count == 1
    p.client.operations.get.return_value = (
        types.UploadToFileSearchStoreOperation.model_validate(
            {
                "name": "operations/test",
                "done": True,
                "response": {"document_name": "fileSearchStores/test/documents/one"},
            }
        )
    )
    assert rag.finish_index(identity).endswith("/one")
    assert rag.index(identity, allow_indexing=True).endswith("/one")
    rag.delete(identity)
    assert storage.documents() == []
    p.client.file_search_stores.documents.delete.assert_called_once()


def test_file_search_uses_registered_version_when_no_public_uri(
    workspace, storage, tmp_path
):
    path = tmp_path / "authorized.md"
    path.write_text("Gordon autorizado", encoding="utf-8")
    identity = workspace.import_document(path, True)
    doc = storage.documents()[0]
    storage.put_document({**doc, "remote_name": "fileSearchStores/test/documents/one"})
    response = sdk_response(
        candidates=[
            {
                "grounding_metadata": {
                    "grounding_chunks": [
                        {
                            "retrieved_context": {
                                "document_name": "fileSearchStores/test/documents/one",
                                "text": "Gordon exige Ke > g",
                            }
                        }
                    ]
                }
            }
        ]
    )
    p = provider(storage, response)
    hit = GeminiFileSearchRetriever(p, storage, "fileSearchStores/test").search(
        "Gordon"
    )[0]
    assert hit.version == doc["version"]
    assert hit.sources[0].uri == "nexo://documents/" + identity


def test_disable_blocks_even_injected_client_and_invalid_environment_is_safe(
    storage, monkeypatch, tmp_path
):
    p = provider(storage, enabled=False)
    with pytest.raises(IntelligenceError, match="desativado"):
        p.synthesize("test")
    p.client.models.generate_content.assert_not_called()
    monkeypatch.setenv("NEXO_AI_DAILY_REQUEST_LIMIT", "invalid")
    settings = AISettings.from_environment(tmp_path / "absent.env")
    assert not settings.enabled
    assert settings.configuration_error
