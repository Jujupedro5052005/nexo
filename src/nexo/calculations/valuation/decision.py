"""Conditional price scenarios; no forecasts or personalized trading instructions."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain._validation import validate_decimal
from nexo.domain.models.market_data import PriceHistory


@dataclass(frozen=True)
class DecisionScenario:
    ceiling: Decimal | None
    entry: Decimal | None
    review: Decimal | None
    upside: Decimal | None
    dividend_yield: Decimal | None
    sma_short: Decimal | None
    sma_long: Decimal | None
    trend: str
    reading: str


def decision_scenario(
    current: Decimal | None,
    estimates: tuple[Decimal | None, ...],
    annual_dividend: Decimal | None,
    history: PriceHistory | None,
    margin: Decimal = Decimal("0.20"),
) -> DecisionScenario:
    validate_decimal(margin, "margin")
    if margin >= 1:
        raise ValueError("Margin must be smaller than one.")
    prices = [point.close for point in history.points] if history else []
    valid = [value for value in estimates if value is not None and value > 0]
    with localcontext(
        financial_context(
            [current, annual_dividend, margin, *valid, *prices], count=len(prices)
        )
    ):
        ceiling = min(valid) if valid else None
        entry = ceiling * (1 - margin) if ceiling else None
        upside = ceiling / current - 1 if ceiling and current and current > 0 else None
        dy = (
            annual_dividend / current
            if annual_dividend is not None and current and current > 0
            else None
        )
        short = sum(prices[-20:], Decimal(0)) / 20 if len(prices) >= 20 else None
        long = sum(prices[-60:], Decimal(0)) / 60 if len(prices) >= 60 else None
    trend = "Histórico insuficiente: são necessários 60 fechamentos para MM20 × MM60."
    if short is not None and long is not None:
        trend = (
            "Alta: MM20 acima da MM60"
            if short > long
            else "Baixa: MM20 abaixo da MM60"
            if short < long
            else "Lateral: médias iguais"
        )
    reading = "Sem base suficiente para classificar o preço."
    if current is not None and entry is not None and ceiling is not None:
        reading = (
            "Faixa de estudo de compra: preço atende à margem escolhida. Confira fundamentos e concentração antes de simular."
            if current <= entry
            else "Faixa de espera: há desconto para o teto, mas a margem escolhida ainda não foi atingida."
            if current < ceiling
            else "Faixa de revisão da posição/venda: preço alcançou o teto do cenário. Reavalie a tese e os custos; não é ordem automática."
        )
    return DecisionScenario(
        ceiling, entry, ceiling, upside, dy, short, long, trend, reading
    )
