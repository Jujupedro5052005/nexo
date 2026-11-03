from threading import Lock
from typing import Any

from nexo.application.intelligence.evidence import evidence_appendix
from nexo.application.intelligence.tools import FinancialTools, encode
from nexo.core.cancellation import check_cancelled
from nexo.domain.interfaces.intelligence import (
    IntelligenceProvider,
    IntelligenceStorage,
    KnowledgeRetriever,
)
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    AnalysisResponse,
    IntelligenceError,
    ToolCall,
)


class IntelligenceOrchestrator:
    """One bounded planning round, local execution, then a tool-free synthesis."""

    def __init__(
        self,
        provider: IntelligenceProvider,
        retriever: KnowledgeRetriever,
        tools: FinancialTools,
        storage: IntelligenceStorage,
        *,
        cloud: bool = False,
        enabled: bool = True,
        max_tool_calls: int = 8,
        max_context_bytes: int = 16000,
    ) -> None:
        self.provider, self.retriever, self.tools, self.storage = (
            provider,
            retriever,
            tools,
            storage,
        )
        self.cloud, self.enabled = cloud, enabled
        self.max_tool_calls, self.max_context_bytes = max_tool_calls, max_context_bytes
        self._lock = Lock()

    def ask(self, request: AnalysisRequest) -> AnalysisResponse:
        if not self.enabled:
            raise IntelligenceError(
                "NEXO Intelligence está desativado por NEXO_AI_ENABLED."
            )
        if self.cloud and not request.allow_cloud:
            raise IntelligenceError(
                "Autorize o envio da pergunta, contexto selecionado e evidências ao Gemini."
            )
        if not self._lock.acquire(blocking=False):
            raise IntelligenceError(
                "Aguarde a operação anterior encerrar antes de iniciar outra."
            )
        try:
            return self._ask(request)
        finally:
            self._lock.release()

    def _ask(self, request: AnalysisRequest) -> AnalysisResponse:
        check_cancelled()
        approved = [
            m for m in self.storage.methodologies() if m.review_status == "approved"
        ]
        context: dict[str, Any] = {
            "question": request.question,
            "selected_context": {
                "portfolio_id": request.portfolio_id,
                "symbol": request.symbol,
                "asset_type": request.asset_type,
            },
            "explicit_assumptions": request.assumptions,
            "approved_methodologies": [
                {"id": m.methodology_id, "version": m.version, "name": m.name}
                for m in approved
            ],
            "untrusted_history": [
                m.model_dump(mode="json")
                for m in self.storage.history(request.conversation_id, 4)
            ],
        }
        # Bounded previous messages; operational evidence gets priority in final context.
        for message in context["untrusted_history"]:
            message["text"] = message["text"][:800]
        try:
            knowledge = self.retriever.search(request.question, 3)
            context["knowledge_status"] = "retrieved" if knowledge else "no_matches"
        except IntelligenceError:
            knowledge = ()
            context["knowledge_status"] = (
                "unavailable; do not invent documentary support"
            )
        context["untrusted_knowledge"] = [h.model_dump(mode="json") for h in knowledge]
        plan = (
            list(self.provider.plan(self._compact(context), self.tools.declarations()))
            if self.cloud
            else []
        )
        defaults: list[ToolCall] = []
        if request.portfolio_id:
            defaults.append(
                ToolCall(
                    name="get_portfolio_snapshot",
                    arguments={"portfolio_id": request.portfolio_id},
                )
            )
        if request.symbol:
            defaults.extend(
                ToolCall(name=name, arguments={"symbol": request.symbol})
                for name in (
                    "get_asset_quote",
                    "get_asset_fundamentals",
                    "get_dividend_history",
                )
            )
        # Reject, never silently truncate, an overlong model plan.
        if len(plan) > self.max_tool_calls:
            raise IntelligenceError("Limite de chamadas do agente excedido.")
        unique: dict[str, ToolCall] = {}
        for call in defaults + plan:
            if call.name == "calculate_valuation":
                continue  # Explicit assumptions are handled below, never by the model.
            unique.setdefault(encode(call), call)
        reserve_calculation = bool(request.methodology_id)
        weighted_calls = sum(
            len(call.arguments["symbols"])
            if call.name == "compare_assets"
            and isinstance(call.arguments.get("symbols"), list)
            else 1
            for call in unique.values()
        )
        if weighted_calls + reserve_calculation > self.max_tool_calls:
            raise IntelligenceError(
                "Limite de ferramentas excedido. Selecione menos contexto ou simplifique a pergunta."
            )
        evidence = [self.tools.execute(call, request) for call in unique.values()]
        if request.methodology_id:
            args = {
                **request.assumptions,
                "method": request.methodology_id,
                "asset_type": request.asset_type,
            }
            # A supplied quote cannot override the current operational evidence.
            args.pop("quote", None)
            args.pop("quote_source", None)
            quote = next(
                (
                    r.data
                    for r in evidence
                    if r.name == "get_asset_quote"
                    and r.available
                    and request.symbol
                    and r.data.get("asset", {}).get("symbol") == request.symbol.upper()
                ),
                None,
            )
            if quote and quote.get("currency") == "BRL":
                args.update(
                    quote=quote["price"],
                    quote_source=f"{quote['source']} · {quote.get('market_time')} · consultada {quote['retrieved_at']}",
                )
            evidence.append(
                self.tools.execute(
                    ToolCall(name="calculate_valuation", arguments=args), request
                )
            )
        context["evidence"] = [r.model_dump(mode="json") for r in evidence]
        # Keep source metadata in the answer; no retrieved text gets system privileges.
        answer = self.provider.synthesize(self._compact(context))
        answer += evidence_appendix(evidence, knowledge)
        if context["knowledge_status"].startswith("unavailable"):
            answer += "\n\nA recuperação documental falhou nesta consulta; a análise usa somente as evidências operacionais disponíveis."
        check_cancelled()
        self.storage.save_turn(request.conversation_id, request.question, answer)
        return AnalysisResponse(
            markdown=answer,
            evidence=tuple(evidence),
            knowledge=knowledge,
            mode="gemini" if self.cloud else "offline",
        )

    def _compact(self, context: dict[str, Any]) -> str:
        serialized = encode(context)
        if len(serialized.encode()) > self.max_context_bytes - 2500:
            context = {**context, "untrusted_history": [], "untrusted_knowledge": []}
            serialized = encode(context)
        if len(serialized.encode()) > self.max_context_bytes - 2500:
            # Return an actionable failure rather than cutting JSON or financial evidence.
            raise IntelligenceError(
                "Evidências excedem o contexto permitido. Consulte um ativo ou uma ferramenta por vez."
            )
        return serialized
