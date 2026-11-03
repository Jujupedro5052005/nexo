import re
from collections.abc import Callable
from decimal import Decimal
from threading import Lock
from typing import Any

from nexo.application.intelligence.deep_analysis import DeepAnalysis, compact_report
from nexo.application.intelligence.synthesis_quality import validate_synthesis
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
        data_mode: str = "normal",
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
        self.data_mode = data_mode
        self.deep = DeepAnalysis(tools)
        self.progress: Callable[[str], None] = lambda _: None

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
        question_symbols = tuple(
            dict.fromkeys(
                re.findall(r"\b[A-Z][A-Z0-9]{3}\d{1,2}\b", request.question.upper())
            )
        )
        if question_symbols:
            request = request.model_copy(
                update={
                    "symbol": question_symbols[0],
                    "focus_symbols": question_symbols,
                }
            )
        previous = self.storage.get_state("conversation:" + request.conversation_id)
        same_scope = previous.get("portfolio_id") == request.portfolio_id and (
            not request.symbol or request.symbol == previous.get("symbol")
        )
        if (
            same_scope
            and previous
            and (
                not question_symbols
                or question_symbols == tuple(previous.get("focus_symbols", ()))
            )
            and any(
                word in request.question.casefold()
                for word in (
                    "anterior",
                    "refaça",
                    "crescimento",
                    "margem de segurança",
                    "por que chegou",
                    "mais baratos",
                    "qual deles",
                    "outra metodologia",
                )
            )
        ):
            changes: dict[str, Any] = {
                "symbol": request.symbol or previous.get("symbol", ""),
                "analysis_mode": previous.get("analysis_mode", "chat"),
                "focus_symbols": previous.get("focus_symbols", ()),
            }
            premises = {**previous.get("assumptions", {}), **request.assumptions}
            margin = re.search(
                r"margem[^\d]{0,30}(\d+(?:[.,]\d+)?)\s*%", request.question.casefold()
            )
            if margin:
                premises["safety_discount"] = str(
                    Decimal(margin.group(1).replace(",", ".")) / 100
                )
            if "crescimento" in request.question.casefold() and any(
                w in request.question.casefold() for w in ("cair", "menor", "reduza")
            ):
                premises["growth"] = str(
                    Decimal(str(premises.get("growth", "0.03"))) - Decimal("0.01")
                )
            changes["assumptions"] = premises
            request = AnalysisRequest.model_validate(
                {**request.model_dump(), **changes}
            )
        explicit_deep = request.portfolio_id is not None and any(
            w in request.question.casefold()
            for w in (
                "analise toda",
                "analise minha carteira",
                "analise a minha carteira",
                "carteira inteira",
                "todas as posições",
                "posições merecem",
                "riscos na minha carteira",
            )
        )
        explicit_deep = explicit_deep and (
            not question_symbols
            or any(
                w in request.question.casefold()
                for w in ("analise toda", "carteira inteira", "todas as posições")
            )
        )
        conceptual_question = any(
            word in request.question.casefold()
            for word in ("explique", "o que é", "conceito", "como funciona")
        )
        asset_analysis = bool(
            question_symbols
        ) and not request.question.casefold().startswith("consulte ")
        if explicit_deep or asset_analysis:
            changes = {"analysis_mode": "deep"}
            if explicit_deep:
                changes["focus_symbols"] = ()
                changes["symbol"] = ""
            else:
                changes["focus_symbols"] = question_symbols
                if len(question_symbols) == 1:
                    changes["symbol"] = question_symbols[0]
            request = AnalysisRequest.model_validate(
                {**request.model_dump(), **changes}
            )
        if (
            conceptual_question
            and not question_symbols
            and not any(
                w in request.question.casefold()
                for w in ("resultado", "anterior", "chegou", "conclusão")
            )
        ):
            request = request.model_copy(
                update={
                    "analysis_mode": "chat",
                    "focus_symbols": (),
                    "methodology_id": "",
                }
            )
        if request.analysis_mode == "deep":
            return self._deep(request)
        approved = [
            m for m in self.storage.methodologies() if m.review_status == "approved"
        ]
        context: dict[str, Any] = {
            "question": request.question,
            "selected_context": {
                "data_mode": self.data_mode,
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
        if previous and not same_scope:
            context["untrusted_history"] = []
        elif previous.get("analysis"):
            context["previous_analysis"] = previous["analysis"]
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
        conceptual = any(
            word in request.question.casefold()
            for word in ("explique", "o que é", "conceito", "como funciona")
        ) and not any(
            word in request.question.casefold()
            for word in ("minha carteira", "meu ativo", "minhas posições")
        )
        if conceptual:
            plan = []  # A conceptual explanation needs no market calls, even if proposed.
        if request.portfolio_id and not conceptual:
            defaults.append(
                ToolCall(
                    name="get_portfolio_snapshot",
                    arguments={"portfolio_id": request.portfolio_id},
                )
            )
        if request.symbol and not conceptual:
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
        if context["knowledge_status"].startswith("unavailable"):
            answer += "\n\nA recuperação documental falhou nesta consulta; a análise usa somente as evidências operacionais disponíveis."
        check_cancelled()
        self.storage.save_turn(request.conversation_id, request.question, answer)
        self.storage.set_state(
            "conversation:" + request.conversation_id,
            {
                "portfolio_id": request.portfolio_id,
                "symbol": request.symbol,
                "analysis_mode": request.analysis_mode,
                "focus_symbols": request.focus_symbols,
                "assumptions": request.assumptions,
            },
        )
        return AnalysisResponse(
            markdown=answer,
            evidence=tuple(evidence),
            knowledge=knowledge,
            mode="gemini" if self.cloud else "offline",
        )

    def _deep(self, request: AnalysisRequest) -> AnalysisResponse:
        self.progress("Investigando carteira e dados financeiros")
        report = self.deep.run(request, progress=self.progress)
        report["data_mode"] = self.data_mode
        context: dict[str, Any] = {
            "question": request.question,
            "data_mode": self.data_mode,
            "analysis": compact_report(report),
            "untrusted_knowledge": [],
            "evidence": [],
            "instructions": "Responda diretamente à pergunta, começando pelo parecer e seu motivo principal. Interprete fundamentos, cotação, cenários e posição. A triagem local e o limiar ilustrativo de concentração não determinam sua conclusão: confronte as evidências. Explique riscos e o que faria rever o parecer. Não calcule números novos nem invente macro, pares ou setores. Não exponha nomes de ferramentas, IDs, hashes ou JSON. Não se limite a encaminhar para o relatório.",
        }
        previous = self.storage.get_state("conversation:" + request.conversation_id)
        if (
            previous.get("portfolio_id") == request.portfolio_id
            and (not request.symbol or request.symbol == previous.get("symbol"))
            and previous.get("analysis")
            and any(
                w in request.question.casefold()
                for w in (
                    "anterior",
                    "outra metodologia",
                    "por que",
                    "qual deles",
                    "mais baratos",
                )
            )
        ):
            context["previous_analysis"] = {
                "label": "Snapshot anterior, não fonte de cotação atual",
                "assets": [
                    {
                        k: a.get(k)
                        for k in (
                            "symbol",
                            "verdict",
                            "scenarios",
                            "estimated_ceiling_gap",
                        )
                    }
                    for a in previous["analysis"]["assets"]
                ],
            }
        if (
            self.cloud
            and request.allow_estimates
            and hasattr(self.provider, "propose_assumptions")
        ):
            self.progress("Construindo hipóteses estimadas e recalculando cenários")
            try:
                proposal = self.provider.propose_assumptions(encode(context))
            except IntelligenceError:
                proposal = None
                report["issues"].append(
                    "Premissas do modelo indisponíveis; usadas apenas faixas ilustrativas Nexo."
                )
            if proposal:
                report = self.deep.run(
                    request, proposal=proposal, progress=self.progress
                )
                report["data_mode"] = self.data_mode
                context["analysis"] = compact_report(report)
        try:
            knowledge = self.retriever.search(
                request.question + " valuation carteira risco", 3
            )
            context["untrusted_knowledge"] = [
                h.model_dump(mode="json") for h in knowledge
            ]
        except IntelligenceError:
            knowledge = ()
            report["issues"].append(
                "Biblioteca remota indisponível; sem fundamentação documental nesta consulta."
            )
        self.progress("Sintetizando parecer e relatório auditável")
        mode = "gemini" if self.cloud else "offline"
        local_answer = "### Pareceres condicionais · análise local\n\n" + "\n\n".join(
            f"**{a['symbol']} — {a['verdict']}**\n\n" + " ".join(a["reasons"])
            for a in report["assets"]
        )
        if self.cloud:
            answer = self.provider.synthesize(self._compact(context))
            validate_synthesis(
                answer, knowledge, [a["symbol"] for a in report["assets"]]
            )
        else:
            answer = local_answer
            if not report["assets"]:
                answer += (
                    "Selecione uma carteira com posições ou um ativo para investigar."
                )
        if not self.cloud:
            answer += "\n\nModo local: cálculos e dados disponíveis, sem interpretação conversacional Gemini. Cenários estimados podem ser revistos na análise completa."
        if self.data_mode == "demo":
            answer = "**DEMO · registros fictícios de demonstração.**\n\n" + answer
        check_cancelled()
        self.storage.save_turn(request.conversation_id, request.question, answer)
        self.storage.set_state(
            "conversation:" + request.conversation_id,
            {
                "portfolio_id": request.portfolio_id,
                "symbol": request.symbol,
                "analysis_mode": "deep",
                "focus_symbols": request.focus_symbols,
                "assumptions": request.assumptions,
                "analysis": compact_report(report),
            },
        )
        return AnalysisResponse(
            markdown=answer,
            knowledge=knowledge,
            mode=mode,
            report=report,
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
