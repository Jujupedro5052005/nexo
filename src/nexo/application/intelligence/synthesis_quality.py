import re

from nexo.domain.models.intelligence import IntelligenceError, KnowledgeHit


def validate_synthesis(
    text: str, knowledge: tuple[KnowledgeHit, ...], symbols: list[str]
) -> None:
    """Minimal acceptance guards, not a proof of financial correctness."""
    normalized = re.sub(r"\s+", " ", text.casefold())
    for hit in knowledge:
        excerpt = re.sub(r"\s+", " ", hit.text.casefold()).strip()
        if len(excerpt) >= 300 and excerpt in normalized:
            raise IntelligenceError(
                "Síntese reproduziu um trecho longo da fonte sem interpretação suficiente."
            )
    if symbols and not any(s.casefold() in normalized for s in symbols):
        raise IntelligenceError(
            "Síntese não relacionou a conclusão aos ativos investigados."
        )
    if symbols and not any(
        term in normalized
        for term in (
            "favorável",
            "aguard",
            "reavali",
            "redu",
            "rebalance",
            "insuficien",
            "insuficiên",
            "ampliar",
            "neutro",
            "manter",
            "acompanhar",
            "compr",
            "vend",
        )
    ):
        raise IntelligenceError(
            "Síntese não apresentou parecer direcional ou insuficiência de dados."
        )
    if (
        "geração dividendos" in normalized
        and any(
            term in normalized
            for term in ("segundo o canal", "método do canal", "ensinado no canal")
        )
        and not any("youtube.com" in s.uri for hit in knowledge for s in hit.sources)
    ):
        raise IntelligenceError(
            "Atribuição ao canal não sustentada pelas fontes recuperadas."
        )
