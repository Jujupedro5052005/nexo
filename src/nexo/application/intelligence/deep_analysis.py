"""Bounded investigation over existing services. No model-generated executable formulas."""

import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from nexo.application.intelligence.tools import FinancialTools, json_data
from nexo.calculations.risk.correlation import aligned_correlation
from nexo.calculations.risk.history import historical_risk
from nexo.calculations.valuation.bank import bank_residual_value
from nexo.calculations.valuation.intelligence import (
    ValuationInputs,
    calculate_valuation,
)
from nexo.core.cancellation import check_cancelled
from nexo.domain.models.asset import Asset
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    IntelligenceError,
    ScenarioProposal,
    ToolCall,
    utc_now,
)
from nexo.domain.models.market_data import HistoricalPrice, PriceHistory

# Small, explicitly curated classification, never infer FII from the suffix 11.
# Unknown tickers remain unclassified; this registry is not a complete B3 universe.
SECTORS = {
    "ITUB": ("Bancos", "bank", "https://www.itau.com.br/relacoes-com-investidores/"),
    "BBAS": ("Bancos", "bank", "https://ri.bb.com.br/"),
    "BBDC": ("Bancos", "bank", "https://www.bradescori.com.br/"),
    "PETR": ("Petróleo e gás", "stock", "https://www.investidorpetrobras.com.br/"),
    "PRIO": ("Petróleo e gás", "stock", "https://ri.prio3.com.br/"),
    "VALE": ("Mineração", "stock", "https://vale.com/investors"),
    "TAEE": ("Energia elétrica", "stock", "https://ri.taesa.com.br/"),
    "EGIE": ("Energia elétrica", "stock", "https://www.engie.com.br/investidores/"),
    "BBSE": (
        "Seguros e participações",
        "insurer",
        "https://www.bbseguridaderi.com.br/",
    ),
    "ITSA": ("Holdings diversificadas", "stock", "https://ri.itausa.com.br/"),
    "B3SA": ("Infraestrutura financeira", "stock", "https://ri.b3.com.br/"),
}


def classify(symbol: str) -> tuple[str, str, str]:
    return next(
        (v for prefix, v in SECTORS.items() if symbol.startswith(prefix)),
        ("Não classificado", "unknown", ""),
    )


def decimal_or_none(value: Any) -> Decimal | None:
    try:
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (ValueError, ArithmeticError):
        return None


class DeepAnalysis:
    def __init__(
        self, tools: FinancialTools, *, max_assets: int = 20, max_calls: int = 100
    ) -> None:
        self.tools, self.max_assets, self.max_calls = tools, max_assets, max_calls
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    def run(
        self,
        request: AnalysisRequest,
        *,
        proposal: ScenarioProposal | None = None,
        progress: Callable[[str], None] = lambda _: None,
    ) -> dict[str, Any]:
        check_cancelled()
        progress("Preparando posições e exposição")
        snapshot = None
        positions: dict[str, Any] = {}
        if request.portfolio_id:
            ledger = self.tools.positions.execute(request.portfolio_id)
            if not request.focus_symbols and (
                len(ledger.positions) > self.max_assets
                or 1 + len(ledger.positions) * 4 > self.max_calls
            ):
                raise IntelligenceError(
                    "Carteira excede o limite de investigação; reduza o escopo antes de consultar mercado."
                )
            result = self.tools.execute(
                ToolCall(
                    name="get_portfolio_snapshot",
                    arguments={"portfolio_id": request.portfolio_id},
                ),
                request,
            )
            if not result.available:
                raise IntelligenceError(
                    "Não foi possível reconstruir a carteira selecionada."
                )
            snapshot = result.data
            positions = {
                p["position"]["asset"]["symbol"]: p
                for p in snapshot["valuation"]["positions"]
            }
        mentioned = re.findall(r"\b[A-Z][A-Z0-9]{3}\d{1,2}\b", request.question.upper())
        symbols = list(request.focus_symbols or tuple(mentioned))
        if request.portfolio_id and any(
            w in request.question.casefold()
            for w in ("analise toda", "carteira inteira", "todas as posições")
        ):
            symbols = list(positions)
        if not symbols and request.symbol:
            symbols = [request.symbol]
        if not symbols and request.analysis_mode == "deep":
            symbols = list(positions)
        for symbol in mentioned:
            if symbol not in symbols:
                symbols.append(symbol)
        if (
            request.symbol
            and not request.focus_symbols
            and not mentioned
            and request.symbol not in symbols
        ):
            symbols.append(request.symbol)
        # A budget applies to the whole explicit run; never silently skip remaining assets.
        if len(symbols) > self.max_assets or 1 + len(symbols) * 4 > self.max_calls:
            raise IntelligenceError(
                f"Análise limitada a {self.max_assets} ativos e {self.max_calls} consultas. Divida o escopo explicitamente."
            )
        report: dict[str, Any] = {
            "portfolio_id": request.portfolio_id,
            "created_at": utc_now().isoformat(),
            "snapshot": snapshot,
            "assets": [],
            "issues": [],
            "policy_version": "nexo-scenarios-2.0",
            "calls": 1 if snapshot else 0,
            "sector_exposure": {},
            "macro": "Taxas, inflação e notícias atuais não consultadas; não são fatos deste relatório.",
        }
        weights = {
            p["asset"]["symbol"]: p["weight"]
            for p in (snapshot or {}).get("concentration", {}).get("weights", [])
        }
        for index, symbol in enumerate(symbols):
            check_cancelled()
            progress(f"Investigando {symbol} · {index + 1}/{len(symbols)}")
            cached = self._cache.get(symbol)
            if cached and (utc_now() - cached[0]).total_seconds() < 300:
                evidence = cached[1]
            else:
                evidence = {}
                for name in (
                    "get_asset_quote",
                    "get_asset_fundamentals",
                    "get_dividend_history",
                    "get_asset_price_history",
                ):
                    arguments: dict[str, Any] = {"symbol": symbol}
                    if name == "get_asset_price_history":
                        arguments["period"] = "1y"
                    result = self.tools.execute(
                        ToolCall(name=name, arguments=arguments), request
                    )
                    evidence[name] = result.model_dump(mode="json")
                    report["calls"] += 1
                self._cache[symbol] = (utc_now(), evidence)
                if len(self._cache) > 64:
                    self._cache.pop(next(iter(self._cache)))
            asset = self._asset(
                symbol,
                evidence,
                positions.get(symbol),
                weights.get(symbol),
                request,
                proposal,
            )
            report["assets"].append(asset)
            if asset["weight"] is not None:
                sector = asset["sector"]
                report["sector_exposure"][sector] = str(
                    Decimal(report["sector_exposure"].get(sector, "0"))
                    + Decimal(asset["weight"])
                )
        report["priorities"] = [
            {"symbol": a["symbol"], "verdict": a["verdict"], "reason": a["reasons"]}
            for a in sorted(
                report["assets"],
                key=lambda a: (
                    a["verdict"] != "Evitar ampliar posição",
                    -(decimal_or_none(a["weight"]) or Decimal(0)),
                ),
            )
        ]
        report["correlations"] = []
        for i, left in enumerate(report["assets"]):
            for right in report["assets"][i + 1 :]:
                lh, rh = left["history"], right["history"]
                correlation = None
                if (
                    lh.get("split_adjusted") is True
                    and rh.get("split_adjusted") is True
                ):
                    lpoints = {
                        p["timestamp"][:10]: Decimal(p["close"])
                        for p in lh.get("points", [])
                    }
                    rpoints = {
                        p["timestamp"][:10]: Decimal(p["close"])
                        for p in rh.get("points", [])
                    }
                    correlation = aligned_correlation(lpoints, rpoints)
                report["correlations"].append(
                    {
                        "left": left["symbol"],
                        "right": right["symbol"],
                        "value": str(correlation) if correlation is not None else None,
                        "reason": "Retornos alinhados; relação histórica, não causal."
                        if correlation is not None
                        else "Exige histórico com ajuste confirmado, 20 retornos alinhados e variância positiva.",
                    }
                )
        return report

    def _asset(
        self,
        symbol: str,
        evidence: dict[str, Any],
        position: Any,
        weight: str | None,
        request: AnalysisRequest,
        proposal: ScenarioProposal | None,
    ) -> dict[str, Any]:
        def data(name: str) -> dict[str, Any]:
            record = evidence.get(name, {})
            return record.get("data") or {} if record.get("available") else {}

        quote = data("get_asset_quote")
        f = data("get_asset_fundamentals")
        dividends = data("get_dividend_history")
        history = data("get_asset_price_history")
        sector, asset_type, classification_source = classify(symbol)
        issues = [
            r.get("error") or "Dado indisponível"
            for r in evidence.values()
            if not r["available"]
        ]
        if any(
            e.get("kind") == "CASH_DISTRIBUTION" for e in dividends.get("events", [])
        ):
            issues.append(
                "Fonte informa distribuição em dinheiro sem separar dividendos/JCP; cenários são brutos e a espécie não foi inventada."
            )
        if quote and not quote.get("market_time"):
            issues.append(
                "Horário efetivo da cotação não informado; consulta não comprova atualização de mercado."
            )
        if f.get("stale_snapshot") or quote.get("stale_snapshot"):
            issues.append("Snapshot sinalizado como antigo; confirmar atualização.")
        if not f.get("reference_date"):
            issues.append("Período fiscal não informado.")
        scenarios = []
        if request.allow_estimates and asset_type != "unknown":
            scenarios = self._scenarios(
                quote, f, dividends, asset_type, proposal, request.assumptions
            )
        risk: Any = None
        points = history.get("points", [])
        if points:
            try:
                h = PriceHistory(
                    Asset(symbol),
                    tuple(
                        HistoricalPrice(
                            datetime.fromisoformat(p["timestamp"]), Decimal(p["close"])
                        )
                        for p in points
                    ),
                    "1y",
                    datetime.fromisoformat(history["retrieved_at"]),
                    source=history.get("source", "não informado"),
                )
                risk = json_data(historical_risk(h))
            except (ValueError, KeyError, ArithmeticError):
                issues.append(
                    "Histórico incompatível para risco; não foi preenchido com zeros."
                )
        verdict, reasons = (
            "Dados insuficientes",
            ["Valuation, qualidade e risco exigem evidências complementares."],
        )
        base = next((s for s in scenarios if s["label"] == "base"), None)
        q = decimal_or_none(quote.get("price"))
        if base and q and quote.get("currency") == "BRL":
            ceiling = Decimal(base["ceiling_price"])
            verdict = (
                "Favorável no cenário estimado" if q < ceiling else "Neutro / aguardar"
            )
            reasons = [
                f"Cotação comparada ao preço teto do cenário base ({ceiling:.2f} BRL); hipóteses não são fatos de mercado."
            ]
            if issues:
                verdict = "Aguardar confirmação dos dados"
                reasons.append(
                    "Datas/qualidade limitam o parecer; simulação permanece disponível."
                )
        if weight is not None and Decimal(weight) > Decimal("0.25"):
            verdict = "Evitar ampliar posição"
            reasons = [
                "Peso acima de 25%, limite ilustrativo configurado na política Nexo, não regra universal nem motivo automático de venda.",
                *reasons,
            ]
        cross_checks = []
        eps = decimal_or_none(f.get("eps"))
        if (
            request.allow_estimates
            and asset_type != "unknown"
            and eps
            and eps > 0
            and any(
                m.methodology_id == "multiples" and m.review_status == "approved"
                for m in self.tools.storage.methodologies()
            )
        ):
            try:
                inputs = ValuationInputs(
                    method="multiples",
                    metric="eps",
                    metric_per_share=eps,
                    reference_multiple=Decimal(10),
                    comparability_note="Referência ilustrativa Nexo de 10 vezes; não é mediana de pares observada.",
                    safety_discount=Decimal(
                        str(request.assumptions.get("safety_discount", "0.20"))
                    ),
                )
                cross_checks.append(
                    {
                        **json_data(calculate_valuation(inputs)),
                        "assumption_kind": "estimated",
                        "justification": inputs.comparability_note,
                    }
                )
            except (ValueError, ArithmeticError):
                pass
        gap = str(Decimal(base["ceiling_price"]) / q - 1) if base and q else None
        return {
            "symbol": symbol,
            "sector": sector,
            "asset_type": asset_type,
            "classification_source": classification_source,
            "weight": weight,
            "position": position,
            "quote": quote,
            "fundamentals": f,
            "dividends": dividends,
            "history": history,
            "risk": risk,
            "scenarios": scenarios,
            "cross_checks": cross_checks,
            "estimated_ceiling_gap": gap,
            "verdict": verdict,
            "reasons": reasons,
            "confidence": "limitada"
            if issues or not scenarios
            else "condicional às premissas",
            "issues": issues,
            "review_conditions": [
                "Atualizar cotação e período fiscal",
                "Rever sustentabilidade dos lucros/proventos e premissas de desconto",
                "Recalcular se peso, caixa, tese ou cenário econômico mudarem",
            ],
            "evidence": evidence,
        }

    def _scenarios(
        self,
        quote: dict[str, Any],
        f: dict[str, Any],
        dividends: dict[str, Any],
        asset_type: str,
        proposal: ScenarioProposal | None,
        user: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if quote.get("currency") not in {None, "BRL"}:
            return []
        # No zero substitution, JCP mixing, or inferred tax rate.
        events = [
            e
            for e in dividends.get("events", [])
            if e.get("kind") in {"DIVIDENDO", "CASH_DISTRIBUTION"}
            and e.get("verified") is not False
            and e.get("currency", "BRL") == "BRL"
        ]
        annual = (
            sum((Decimal(e["amount"]) for e in events), Decimal(0)) if events else None
        )
        bank = (
            asset_type == "bank"
            and decimal_or_none(f.get("bvps"))
            and decimal_or_none(f.get("roe"))
        )
        executable = "bank_residual" if bank else "target_yield"
        if not any(
            m.methodology_id == executable and m.review_status == "approved"
            for m in self.tools.storage.methodologies()
        ):
            return []
        if not bank and (annual is None or annual <= 0):
            return []
        defaults = [
            ("conservador", "0.16", "0.02", "0.10"),
            ("base", "0.14", "0.03", "0.08"),
            ("otimista", "0.12", "0.04", "0.06"),
        ]
        configs = (
            [
                (
                    s.label,
                    str(s.required_return),
                    str(s.growth),
                    str(s.target_yield),
                    s.justification,
                )
                for s in proposal.scenarios
            ]
            if proposal
            else [
                (
                    label,
                    ke,
                    g,
                    y,
                    "Faixa ilustrativa da política Nexo v2; sem afirmar que estas são taxas atuais ou justas.",
                )
                for label, ke, g, y in defaults
            ]
        )
        results = []
        discount = Decimal(str(user.get("safety_discount", "0.20")))
        if (
            not discount.is_finite()
            or not 0 <= discount < 1
            or int(discount.as_tuple().exponent) < -12
        ):
            raise IntelligenceError(
                "Desconto de segurança deve ser fração entre zero e um, com até 12 casas."
            )
        for label, ke, g, target, rationale in configs:
            try:
                ke = str(user.get("required_return", ke))
                g = str(user.get("growth", g))
                target = str(user.get("target_yield", target))
                if bank:
                    value = bank_residual_value(
                        Decimal(f["bvps"]), Decimal(f["roe"]), Decimal(ke), Decimal(g)
                    )
                    result = {
                        "theoretical_value": str(value),
                        "ceiling_price": str(value * (1 - discount)),
                        "formula": "VPA × (ROE − g) / (Ke − g)",
                        "method": "bank_residual",
                        "inputs": {
                            "bvps": f["bvps"],
                            "roe": f["roe"],
                            "required_return": ke,
                            "growth": g,
                        },
                    }
                else:
                    inputs = ValuationInputs(
                        method="target_yield",
                        expected_dividend=Decimal(str(user["expected_dividend"]))
                        if "expected_dividend" in user
                        else annual,
                        target_yield=Decimal(target),
                        dividend_source=f"{dividends.get('source')} · {dividends.get('start_date')} a {dividends.get('end_date')}",
                        sustainability_note="Repetição hipotética da janela histórica; sustentabilidade não confirmada.",
                        safety_discount=discount,
                    )
                    result = json_data(calculate_valuation(inputs))
                results.append(
                    {
                        **result,
                        "label": label,
                        "assumption_kind": "estimated",
                        "justification": rationale,
                        "origin": "gemini_estimate" if proposal else "nexo_policy",
                        "safety_discount": str(discount),
                        "observed_inputs_source": f.get("source")
                        if bank
                        else dividends.get("source"),
                        "premises": [
                            {
                                "name": "roe" if bank else "expected_dividend",
                                "kind": "observed"
                                if bank
                                else "user"
                                if "expected_dividend" in user
                                else "estimated",
                                "value": f.get("roe")
                                if bank
                                else str(user.get("expected_dividend", annual)),
                                "source": f.get("source") if bank else None,
                                "justification": "ROE observado; estabilidade futura é hipótese."
                                if bank
                                else "Repetição futura estimada ou valor explícito do usuário.",
                            },
                            *(
                                [
                                    {
                                        "name": "growth",
                                        "kind": "user"
                                        if "growth" in user
                                        else "estimated",
                                        "value": g,
                                        "justification": rationale,
                                    }
                                ]
                                if bank
                                else []
                            ),
                            {
                                "name": "bvps" if bank else "historical_distribution",
                                "kind": "observed" if bank else "derived",
                                "source": f.get("source")
                                if bank
                                else dividends.get("source"),
                                "value": f.get("bvps") if bank else str(annual),
                            },
                            {
                                "name": "required_return" if bank else "target_yield",
                                "kind": "user"
                                if ("required_return" if bank else "target_yield")
                                in user
                                else "estimated",
                                "value": ke if bank else target,
                                "justification": rationale,
                            },
                            {
                                "name": "safety_discount",
                                "kind": "user"
                                if "safety_discount" in user
                                else "estimated",
                                "value": str(discount),
                                "justification": "Desconto de segurança explícito da política Nexo ou do usuário.",
                            },
                        ],
                    }
                )
            except (ValueError, ArithmeticError):
                continue
        if len(results) != 3:
            return []
        results.sort(key=lambda s: Decimal(str(s["ceiling_price"])))
        return [
            {**s, "label": label}
            for label, s in zip(
                ("conservador", "base", "otimista"), results, strict=True
            )
        ]


def compact_report(report: dict[str, Any]) -> dict[str, Any]:
    """LLM sees compact facts/scenarios; full numerical traces stay local for inspection."""
    assets = []
    for a in report["assets"]:
        entry = {
            k: a[k]
            for k in (
                "symbol",
                "sector",
                "weight",
                "verdict",
                "reasons",
                "risk",
                "issues",
                "review_conditions",
            )
        }
        entry["quote"] = {
            k: a["quote"].get(k)
            for k in ("price", "currency", "market_time", "retrieved_at", "source")
        }
        entry["position"] = a.get("position")
        entry["fundamentals"] = {
            k: a["fundamentals"].get(k)
            for k in (
                "eps",
                "bvps",
                "roe",
                "roic",
                "net_margin",
                "net_debt_ebitda",
                "source",
                "reference_date",
            )
        }
        entry["scenarios"] = [
            {
                k: s.get(k)
                for k in (
                    "label",
                    "method",
                    "theoretical_value",
                    "ceiling_price",
                    "justification",
                    "assumption_kind",
                    "inputs",
                    "origin",
                )
            }
            for s in a["scenarios"]
        ]
        entry["cross_checks"] = [
            {
                k: c.get(k)
                for k in (
                    "method",
                    "theoretical_value",
                    "ceiling_price",
                    "assumption_kind",
                    "justification",
                )
            }
            for c in a.get("cross_checks", [])
        ]
        entry["estimated_ceiling_gap"] = a.get("estimated_ceiling_gap")
        assets.append(entry)
    return {
        "portfolio_id": report["portfolio_id"],
        "policy_version": report["policy_version"],
        "sector_exposure": report["sector_exposure"],
        "macro": report["macro"],
        "assets": assets,
        "portfolio_summary": {
            k: report.get("snapshot", {}).get("valuation", {}).get(k)
            for k in (
                "invested_cost",
                "current_market_value",
                "unrealized_profit_loss",
                "unrealized_return",
            )
        }
        if report.get("snapshot")
        else None,
        "concentration": report.get("snapshot", {}).get("concentration")
        if report.get("snapshot")
        else None,
        "correlations": [
            c for c in report.get("correlations", []) if c["value"] is not None
        ][:10],
    }
