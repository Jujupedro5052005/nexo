from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from nexo.application.intelligence.knowledge_service import KnowledgeService
from nexo.application.intelligence.methodologies import builtin_methodologies
from nexo.application.intelligence.orchestrator import IntelligenceOrchestrator
from nexo.application.intelligence.tools import FinancialTools
from nexo.application.intelligence.workspace import IntelligenceWorkspace
from nexo.domain.interfaces.intelligence import IntelligenceProvider, KnowledgeRetriever
from nexo.infrastructure.intelligence.config import AISettings
from nexo.infrastructure.intelligence.knowledge import (
    GeminiFileSearchRetriever,
    LocalKnowledgeRetriever,
)
from nexo.infrastructure.intelligence.providers import (
    GeminiIntelligenceProvider,
    MockIntelligenceProvider,
)
from nexo.infrastructure.intelligence.storage import SqliteIntelligenceStorage


def create_workspace(
    settings: AISettings, storage: SqliteIntelligenceStorage, tools: FinancialTools
) -> IntelligenceWorkspace:
    existing = {(m.methodology_id, m.version) for m in storage.methodologies()}
    for method in builtin_methodologies():
        if (method.methodology_id, method.version) not in existing:
            storage.save_methodology(method)
    provider: IntelligenceProvider
    retriever: KnowledgeRetriever
    local = LocalKnowledgeRetriever(storage)
    if settings.cloud:
        gemini = GeminiIntelligenceProvider(settings, storage)
        provider = gemini
        retriever = (
            GeminiFileSearchRetriever(gemini, storage, settings.file_search_store)
            if settings.file_search_store
            else local
        )
    else:
        provider = MockIntelligenceProvider()
        retriever = local
    orchestrator = IntelligenceOrchestrator(
        provider,
        retriever,
        tools,
        storage,
        cloud=settings.cloud,
        enabled=settings.enabled,
        max_tool_calls=settings.max_tool_calls,
        max_context_bytes=settings.max_input_tokens,
    )

    def status() -> dict[str, Any]:
        usage = storage.usage()
        try:
            rates = [
                Decimal(settings.input_usd_per_million),
                Decimal(settings.output_usd_per_million),
            ]
            upper_cost = (
                str(Decimal(usage["tokens_accounted"]) * max(rates) / Decimal(1000000))
                if all(r.is_finite() and r >= 0 for r in rates)
                else None
            )
        except InvalidOperation:
            upper_cost = None
        return {
            "enabled": settings.enabled,
            "configuration_error": settings.configuration_error,
            "mode": "Gemini" if settings.cloud else "Offline",
            "model": settings.model,
            "key_configured": bool(settings.api_key),
            "project_id": settings.project_id,
            "project_number": settings.project_number,
            "max_input_tokens": settings.max_input_tokens,
            "max_output_tokens": settings.max_output_tokens,
            "daily_request_limit": settings.daily_request_limit,
            "daily_token_limit": settings.daily_token_limit,
            "file_search": settings.file_search_store or "Local · busca textual",
            "usage": usage,
            "estimated_upper_generation_cost_usd": upper_cost,
            "cost_note": "Estimativa conservadora com tarifas configuradas; não inclui embeddings/indexação, impostos ou cobrança efetiva do Google.",
            "storage": str(storage.path),
        }

    def export_analysis(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    return IntelligenceWorkspace(
        orchestrator,
        KnowledgeService(storage, provider),
        storage,
        tools.portfolios,
        lambda path, authorized: local.import_document(path, authorized=authorized),
        export_analysis,
        status,
    )
