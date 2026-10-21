from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True)
class SolvencyResult:
    model: str
    score: Decimal | None
    classification: str
    missing: tuple[str, ...]
    formula: str


# Silva & Victor, supplied article, Quadro 1 pp.5–6. Coefficients operate on ratios.
MODELS = {
    "Elizabetsky": (
        ("net_income", "sales"),
        ("cash", "permanent_assets"),
        ("receivables", "assets"),
        ("inventory", "assets"),
        ("current_liabilities", "assets"),
    ),
    "Kanitz": (
        ("net_income", "equity"),
        ("long_liquidity", "liabilities"),
        ("quick_assets", "current_liabilities"),
        ("current_assets", "current_liabilities"),
        ("liabilities", "equity"),
    ),
    "Matias": (
        ("equity", "assets"),
        ("bank_debt", "current_assets"),
        ("suppliers", "assets"),
        ("current_assets", "current_liabilities"),
        ("operating_income", "gross_profit"),
        ("cash", "assets"),
    ),
}
COEFFICIENTS = {
    "Elizabetsky": ("1.93", "-.20", "1.02", "1.33", "-1.12"),
    "Kanitz": (".05", "1.65", "3.55", "-1.06", "-.33"),
    "Matias": ("23.792", "-8.26", "-9.868", "-.764", "-.535", "9.912"),
}


def insolvency_scores(
    values: dict[str, Decimal], *, nonfinancial: bool, aligned: bool
) -> tuple[SolvencyResult, ...]:
    if not nonfinancial or not aligned:
        raise DomainValidationError(
            "Use somente empresas não financeiras, demonstrações do mesmo período, moeda/escala compatíveis e contas conferidas."
        )
    if any(not v.is_finite() for v in values.values()):
        raise DomainValidationError("Contas devem conter valores finitos.")
    data = dict(values)
    if "current_assets" in data and "long_receivables" in data:
        data["long_liquidity"] = data["current_assets"] + data["long_receivables"]
    if "current_assets" in data and "inventory" in data:
        data["quick_assets"] = data["current_assets"] - data["inventory"]
    results = []
    for model, ratios in MODELS.items():
        missing = tuple(
            sorted({key for pair in ratios for key in pair if key not in data})
        )
        formula = " + ".join(
            f"{c} × ({a}/{b})" for c, (a, b) in zip(COEFFICIENTS[model], ratios)
        )
        bad = tuple(b for _, b in ratios if b in data and data[b] <= 0)
        if missing or bad:
            results.append(
                SolvencyResult(
                    model,
                    None,
                    "Dados ausentes ou denominador não positivo",
                    missing + bad,
                    formula,
                )
            )
            continue
        with localcontext(financial_context(data.values())):
            score = sum(
                (
                    Decimal(c) * data[a] / data[b]
                    for c, (a, b) in zip(COEFFICIENTS[model], ratios)
                ),
                Decimal(0),
            )
        if model == "Kanitz":
            label = (
                "Faixa de solvência do modelo"
                if score > 0
                else "Faixa de insolvência do modelo"
                if score < -3
                else "Penumbra / limite"
            )
        else:
            threshold = Decimal(".5") if model == "Elizabetsky" else Decimal(0)
            label = (
                "Faixa de solvência do modelo"
                if score > threshold
                else "Faixa de insolvência do modelo"
                if score < threshold
                else "No ponto de corte"
            )
        results.append(SolvencyResult(model, score, label, (), formula))
    return tuple(results)
