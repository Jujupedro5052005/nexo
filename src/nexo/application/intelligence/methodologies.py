"""Nexo's reviewed implementations; no attribution to an unprocessed channel."""

from nexo.domain.models.intelligence import Methodology, SourceReference


def builtin_methodologies() -> tuple[Methodology, ...]:
    entries = (
        (
            "gordon",
            "Gordon",
            ("expected_dividend", "required_return", "growth"),
            "D1 / (Ke - g)",
            "Dividendos sustentáveis e crescimento perpétuo constante; D1 é do próximo período.",
            "Ke > g; sensível a pequenas mudanças das taxas.",
        ),
        (
            "target_yield",
            "Dividend Yield alvo",
            ("expected_dividend", "target_yield"),
            "D / yield",
            "Dividendo esperado explicitamente justificado; yield escolhido pelo usuário.",
            "Histórico não é projeção garantida; verificar distribuição recorrente.",
        ),
        (
            "multiples",
            "Múltiplos comparáveis",
            ("metric", "metric_per_share", "reference_multiple"),
            "métrica por ação × múltiplo",
            "P/L sobre LPA ou P/VP sobre VPA; pares comparáveis no mesmo período.",
            "Métrica positiva; para FII apenas VPA; diferenças contábeis e setoriais limitam comparação.",
        ),
    )
    return tuple(
        Methodology(
            methodology_id=identity,
            name=name,
            version=1,
            description=f"Implementação educacional do Nexo: {name}.",
            applicable_asset_types=("stock", "bank", "insurer", "fii"),
            required_inputs=required,
            optional_inputs=("quote", "safety_discount"),
            formula_reference=formula,
            assumptions=(assumption,),
            constraints=(constraint,),
            origin="nexo",
            review_status="approved",
            reviewed_by="Nexo — implementação versionada e testes conhecidos",
            source_references=(
                SourceReference(
                    title="Implementação Nexo (não atribuída a Geração Dividendos)",
                    uri="nexo://calculations/valuation/intelligence",
                ),
            ),
        )
        for identity, name, required, formula, assumption, constraint in entries
    )
