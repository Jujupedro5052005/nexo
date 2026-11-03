from decimal import Decimal
from typing import Any

from nexo.domain.models.intelligence import AnalysisResponse


def display(value: Any, *, percent: bool = False) -> str:
    if value is None:
        return "Indisponível"
    n = Decimal(str(value))
    return f"{n * 100:.2f}%" if percent else f"{n:.2f}"


def report_markdown(response: AnalysisResponse) -> str:
    lines = [
        "# NEXO Intelligence · relatório",
        f"\nGerado: {response.created_at.isoformat()} · modo {response.mode}",
        "\n" + response.markdown,
    ]
    report = response.report
    if report:
        lines += ["\n## Diagnóstico", "\n| Setor | Peso |", "|---|---:|"]
        for sector, weight in report.get("sector_exposure", {}).items():
            lines.append(f"| {sector} | {display(weight, percent=True)} |")
        for pair in report.get("correlations", []):
            lines.append(
                f"\nCorrelação histórica {pair['left']} / {pair['right']}: {display(pair.get('value'))}. {pair['reason']}"
            )
        for asset in report.get("assets", []):
            q = asset["quote"]
            lines += [
                f"\n## {asset['symbol']} — {asset['verdict']}",
                "\n" + " ".join(asset["reasons"]),
                f"\nCotação: {display(q.get('price'))} {q.get('currency', '')}; peso: {display(asset.get('weight'), percent=True)}.",
                f"Fonte: {q.get('source', 'indisponível')} · mercado: {q.get('market_time') or 'horário não informado'} · consulta: {q.get('retrieved_at') or 'não informada'}.",
                "\n| Cenário | Método | Valor teórico BRL | Preço teto BRL |",
                "|---|---|---:|---:|",
            ]
            for scenario in asset["scenarios"]:
                lines.append(
                    f"| {scenario['label']} | {scenario['method']} | {display(scenario.get('theoretical_value'))} | {display(scenario.get('ceiling_price'))} |"
                )
            for scenario in asset["scenarios"]:
                lines.append(
                    f"\nPremissa estimada ({scenario['origin']}): {scenario['justification']}\nFórmula: {scenario.get('formula', 'ver metodologia')}."
                )
                for premise in scenario.get("premises", []):
                    lines.append(
                        f"- {premise['name']}: {premise.get('value', 'não informada')} · {premise['kind']} · fonte/justificativa: {premise.get('source') or premise.get('justification', '')}"
                    )
            risk = asset.get("risk") or {}
            if risk:
                lines.append(
                    "\nRisco do histórico: volatilidade anualizada "
                    + display(risk.get("annual_volatility"), percent=True)
                    + "; drawdown máximo "
                    + display(risk.get("max_drawdown"), percent=True)
                    + f"; {risk.get('observations', 0)} observações. Não é previsão."
                )
            for check in asset.get("cross_checks", []):
                lines.append(
                    f"\nVerificação alternativa ({check['method']}): teto BRL {display(check.get('ceiling_price'))}. {check['justification']}"
                )
            lines += [
                "\nLimitações: " + "; ".join(asset["issues"]),
                "\nRevisar se: " + "; ".join(asset["review_conditions"]),
            ]
    for hit in response.knowledge:
        for source in hit.sources:
            lines.append(
                f"\nFonte metodológica: {source.title} · {source.uri} · versão {hit.version}"
            )
    return "\n".join(lines) + "\n"
