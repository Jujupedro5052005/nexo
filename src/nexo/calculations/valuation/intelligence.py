"""Deterministic, explicit scenario assumptions; rates are fractions, not percent."""

from decimal import Decimal, localcontext
from typing import Literal

from pydantic import Field, model_validator

from nexo.calculations.precision import financial_context
from nexo.calculations.valuation.company import bazin_price, safety_margin
from nexo.domain.models.intelligence import Record, utc_now


class ValuationInputs(Record):
    method: Literal["gordon", "target_yield", "multiples"]
    asset_type: Literal["stock", "bank", "insurer", "fii", "etf", "bond", "crypto"] = (
        "stock"
    )
    expected_dividend: Decimal | None = Field(default=None, ge=0, le=Decimal("1e12"))
    dividend_source: str = Field(default="", max_length=500)
    sustainability_note: str = Field(default="", max_length=1000)
    required_return: Decimal | None = Field(default=None, gt=0, le=1)
    growth: Decimal | None = Field(default=None, gt=-1, lt=1)
    target_yield: Decimal | None = Field(default=None, gt=0, le=1)
    metric: Literal["eps", "bvps"] | None = None
    metric_per_share: Decimal | None = Field(default=None, gt=0, le=Decimal("1e12"))
    reference_multiple: Decimal | None = Field(default=None, gt=0, le=1000)
    comparability_note: str = Field(default="", max_length=1000)
    safety_discount: Decimal = Field(default=Decimal("0.20"), ge=0, lt=1)
    quote: Decimal | None = Field(default=None, gt=0, le=Decimal("1e12"))
    quote_source: str = "Não informada"
    currency: Literal["BRL"] = "BRL"

    @model_validator(mode="after")
    def check_applicability(self) -> "ValuationInputs":
        for value in self.model_dump().values():
            if isinstance(value, Decimal) and int(value.as_tuple().exponent) < -12:
                raise ValueError("Use no máximo 12 casas decimais nas premissas de valuation.")
        if self.asset_type not in {"stock", "bank", "insurer", "fii"}:
            raise ValueError("Metodologia incompatível com esta classe de ativo.")
        if self.method in {"gordon", "target_yield"}:
            if self.expected_dividend is None:
                raise ValueError(
                    "Informe o dividendo esperado por ação/cota; ausência não é zero."
                )
            if not self.dividend_source.strip() or not self.sustainability_note.strip():
                raise ValueError(
                    "Informe origem do dividendo e avaliação da sustentabilidade."
                )
        if self.method == "gordon" and (
            self.required_return is None
            or self.growth is None
            or self.required_return <= self.growth
        ):
            raise ValueError("Gordon exige Ke > g, com ambas as premissas explícitas.")
        if self.method == "target_yield" and self.target_yield is None:
            raise ValueError("Informe o yield alvo.")
        if self.method == "multiples":
            if self.asset_type == "fii" and self.metric != "bvps":
                raise ValueError("Para FII use patrimônio por cota; LPA não é FFO.")
            if (
                self.metric is None
                or self.metric_per_share is None
                or self.reference_multiple is None
                or not self.comparability_note.strip()
            ):
                raise ValueError(
                    "Informe métrica por ação, múltiplo e comparabilidade."
                )
        return self


def calculate_valuation(inputs: ValuationInputs) -> dict[str, object]:
    with localcontext(
        financial_context(
            [v for v in inputs.model_dump().values() if isinstance(v, Decimal)]
        )
    ):
        if inputs.method == "gordon":
            assert inputs.expected_dividend is not None
            assert inputs.required_return is not None and inputs.growth is not None
            value = inputs.expected_dividend / (inputs.required_return - inputs.growth)
            formula = f"{inputs.expected_dividend} / ({inputs.required_return} - {inputs.growth})"
        elif inputs.method == "target_yield":
            assert (
                inputs.target_yield is not None and inputs.expected_dividend is not None
            )
            # Reuse the existing deterministic yield implementation. Zero is explicit.
            value = bazin_price(
                inputs.expected_dividend, inputs.target_yield
            ) or Decimal(0)
            formula = f"{inputs.expected_dividend} / {inputs.target_yield}"
        else:
            assert (
                inputs.metric_per_share is not None
                and inputs.reference_multiple is not None
            )
            value = inputs.metric_per_share * inputs.reference_multiple
            formula = f"{inputs.metric_per_share} × {inputs.reference_multiple}"
        ceiling = value * (1 - inputs.safety_discount)
        margin = safety_margin(value, inputs.quote)
        return {
            "method": inputs.method,
            "theoretical_value": value,
            "ceiling_price": ceiling,
            "quote": inputs.quote,
            "difference_percent": (value / inputs.quote - 1) * 100
            if inputs.quote
            else None,
            "safety_margin": margin.ratio if margin else None,
            "formula": formula,
            "assumptions": inputs.model_dump(mode="json"),
            "calculated_at": utc_now().isoformat(),
            "limitations": "Premissas condicionais; dividendos históricos não garantem distribuição futura. Sem recomendação automática.",
        }


def sensitivity(inputs: ValuationInputs) -> list[dict[str, object]]:
    """Five points varying one premise; +/- 10% are synthetic scenario shocks."""
    axis = {
        "gordon": "required_return",
        "target_yield": "target_yield",
        "multiples": "reference_multiple",
    }[inputs.method]
    base = getattr(inputs, axis)
    points = []
    for change in ("-0.10", "-0.05", "0", "0.05", "0.10"):
        assumption = base * (1 + Decimal(change))
        try:
            candidate = ValuationInputs.model_validate(
                {**inputs.model_dump(), axis: assumption}
            )
        except ValueError:
            points.append({"axis": axis, "input": assumption, "available": False})
            continue
        result = calculate_valuation(candidate)
        points.append(
            {
                "axis": axis,
                "input": assumption,
                "available": True,
                "ceiling_price": result["ceiling_price"],
                "theoretical_value": result["theoretical_value"],
            }
        )
    return points
