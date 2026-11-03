import json
from types import SimpleNamespace

import pytest

from nexo.application.intelligence.synthesis_quality import validate_synthesis
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    IntelligenceError,
    KnowledgeHit,
    QuotaExceeded,
)
from nexo.infrastructure.intelligence.knowledge import GeminiFileSearchRetriever
from nexo.infrastructure.intelligence.providers import MockIntelligenceProvider

from .test_gemini import provider, sdk_response
from .test_mission2 import investigation_data  # noqa: F401 - registered fixture


def proposed(**changes):
    return {
        "scenarios": [
            {
                "label": label,
                "required_return": "0.14",
                "growth": "0.03",
                "target_yield": "0.08",
                "justification": "Hipótese ilustrativa baseada apenas nos dados fornecidos.",
                **changes,
            }
            for label in ("conservador", "base", "otimista")
        ]
    }


def test_gemini_proposes_typed_assumptions_not_observed_facts(storage):
    p = provider(storage, sdk_response(json.dumps(proposed())))
    scenarios = p.propose_assumptions("Dados operacionais identificados")
    assert len(scenarios.scenarios) == 3
    config = p.client.models.generate_content.call_args.kwargs["config"]
    assert config.response_schema is not None
    assert storage.usage()["features"][0][0] == "scenario_proposal"


@pytest.mark.parametrize(
    "changes",
    [
        {"label": "base"},
        {"required_return": "0.06", "growth": "0.06"},
        {"required_return": "NaN"},
        {"justification": "x"},
    ],
)
def test_invalid_proposed_premises_are_not_executed(storage, changes):
    p = provider(storage, sdk_response(json.dumps(proposed(**changes))))
    with pytest.raises(IntelligenceError):
        p.propose_assumptions("Dados identificados")


def test_rag_paste_and_unsupported_attribution_are_rejected():
    excerpt = (
        "Um trecho técnico suficientemente longo deve servir como fundamentação e não substituir a interpretação do relatório. "
        * 5
    )
    hit = KnowledgeHit(document_id="original", version="1", text=excerpt)
    with pytest.raises(IntelligenceError, match="reproduziu"):
        validate_synthesis("ITUB4: aguardar. " + excerpt, (hit,), ["ITUB4"])
    with pytest.raises(IntelligenceError, match="Atribuição"):
        validate_synthesis(
            "ITUB4: aguardar. Segundo o canal Geração Dividendos, este é o método do canal.",
            (),
            ["ITUB4"],
        )
    with pytest.raises(IntelligenceError, match="direcional"):
        validate_synthesis("ITUB4 tem esses indicadores.", (), ["ITUB4"])
    validate_synthesis(
        "ITUB4: aguardar confirmação; o cenário estimado depende do custo de capital informado.",
        (hit,),
        ["ITUB4"],
    )


def test_failed_gemini_keeps_deterministic_report(investigation):
    class FailingProvider(MockIntelligenceProvider):
        def synthesize(self, context):
            raise QuotaExceeded("Limite de geração atingido")

    investigation.orchestrator.provider = FailingProvider()
    investigation.orchestrator.cloud = True
    response = investigation.ask(
        AnalysisRequest(
            question="Analise ITUB4",
            symbol="ITUB4",
            analysis_mode="deep",
            allow_cloud=True,
        )
    )
    assert response.mode == "local-fallback"
    assert response.report["assets"][0]["scenarios"]
    assert "determinístico preservado" in response.markdown


def test_file_search_store_management_is_bounded_and_accounted(storage):
    p = provider(storage)
    p.client.file_search_stores.list.return_value = (
        SimpleNamespace(name=f"fileSearchStores/{i}", display_name=str(i))
        for i in range(100)
    )
    stores = GeminiFileSearchRetriever.list_stores(p)
    assert len(stores) == 20
    p.client.file_search_stores.create.return_value = SimpleNamespace(
        name="fileSearchStores/test"
    )
    assert (
        GeminiFileSearchRetriever.create_store(p, "Nexo teste")
        == "fileSearchStores/test"
    )
    assert storage.usage()["requests"] == 2
    assert storage.usage()["tokens_accounted"] == 0
    p.client.file_search_stores.create.side_effect = RuntimeError("key=supersecret")
    with pytest.raises(IntelligenceError) as error:
        GeminiFileSearchRetriever.create_store(p, "Nexo")
    assert "supersecret" not in str(error.value)


def test_sync_preserves_canonical_catalog_and_small_batch(workspace, storage, tmp_path):
    for i in range(5):
        path = tmp_path / f"authorized-{i}.md"
        path.write_text(f"Gordon exemplo {i}", encoding="utf-8")
        workspace.import_document(path, True)
    p = provider(storage)
    rag = GeminiFileSearchRetriever(p, storage, "fileSearchStores/test")
    submitted = []
    rag.index = lambda identity, allow_indexing: submitted.append(identity) or "pending"
    assert len(rag.sync(limit=2, allow_indexing=True)) == 2
    assert len(submitted) == 2
    assert len(storage.documents()) == 5
    with pytest.raises(IntelligenceError):
        rag.sync(limit=4, allow_indexing=True)


def test_quote_zero_intraday_fields_remain_unavailable(tmp_path):
    from nexo.domain.models.asset import Asset
    from nexo.infrastructure.market_data.adapters.yahoo import YahooFinanceProvider
    from nexo.infrastructure.market_data.policy import ProviderUsage

    yahoo = YahooFinanceProvider(
        ProviderUsage(tmp_path / "usage.json", {"Yahoo Finance": 5})
    )
    quote = yahoo._quote_from_info(
        Asset("ITUB4"),
        {
            "regularMarketPrice": 30,
            "currency": "BRL",
            "regularMarketDayHigh": 0,
            "regularMarketDayLow": 0,
        },
    )
    assert quote.price == 30
    assert quote.day_high is None and quote.day_low is None
    assert quote.market_time is None
