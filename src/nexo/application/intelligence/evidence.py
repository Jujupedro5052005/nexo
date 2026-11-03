"""Deterministic appendix keeps sources and arithmetic independent of LLM prose."""

from urllib.parse import urlparse

from nexo.domain.models.intelligence import KnowledgeHit, ToolResult


def evidence_appendix(
    evidence: list[ToolResult], knowledge: tuple[KnowledgeHit, ...]
) -> str:
    lines = ["\n\n### Evidências verificáveis"]
    for item in evidence:
        lines.append(
            f"- **{item.name}** · consulta {item.queried_at.isoformat()} · {'disponível' if item.available else 'indisponível'}"
        )
        if not item.available:
            lines.append(f"  {item.error}")
        elif isinstance(item.data, dict):
            source = item.data.get("source")
            if source:
                lines.append(
                    f"  Fonte: {source}; referência: {item.data.get('reference_date') or item.data.get('market_time') or 'não informada'}."
                )
            if item.data.get("stale_snapshot"):
                lines.append(
                    "  **Snapshot antigo: verifique a atualização antes de interpretar os valores.**"
                )
            if item.name == "calculate_valuation":
                data = item.data
                lines.extend(
                    [
                        f"\nMemória de cálculo (BRL): `{data['formula']}` = **{data['theoretical_value']}**.",
                        f"Preço teto: **{data['ceiling_price']}**; cotação: **{data['quote'] or 'não informada'}**.",
                        f"Desconto aplicado: {data['assumptions']['safety_discount']} (fração). Margem observada: {data['safety_margin'] if data['safety_margin'] is not None else 'indisponível'} (fração).",
                        "\nSensibilidade sintética: varia uma premissa em −10%, −5%, 0, +5%, +10%; não são previsões.",
                        "\n| Premissa | Entrada (fração para taxas) | Preço teto BRL |",
                        "|---|---:|---:|",
                    ]
                )
                for point in data.get("sensitivity", []):
                    lines.append(
                        f"| {point['axis']} | {point['input']} | {point.get('ceiling_price', 'incompatível')} |"
                    )
                valid = [p for p in data.get("sensitivity", []) if p["available"]]
                if valid:
                    from decimal import Decimal

                    ceilings = [Decimal(p["ceiling_price"]) for p in valid]
                    lines.append(
                        f"\nCenários sintéticos: conservador {min(ceilings)}, base {data['ceiling_price']}, otimista {max(ceilings)} BRL. Demais premissas constantes."
                    )
    for hit in knowledge:
        for source in hit.sources:
            parsed = urlparse(source.uri)
            title = source.title.replace("[", "").replace("]", "").replace("\n", " ")
            if (
                parsed.scheme in {"https", "http"}
                and parsed.netloc
                and not any(c in source.uri for c in "<>[]() \n\r")
            ):
                lines.append(f"- [{title}]({source.uri}) · versão {hit.version}")
            else:
                lines.append(
                    f"- {title} · documento {hit.document_id} · versão {hit.version}"
                )
    return "\n".join(lines)
