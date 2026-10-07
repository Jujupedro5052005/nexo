from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import TYPE_CHECKING

from nexo.calculations.precision import financial_context
from nexo.domain.models.asset import Asset

if TYPE_CHECKING:
    from nexo.calculations.valuation.portfolio import PortfolioValuation


@dataclass(frozen=True, slots=True)
class PositionWeight:
    asset: Asset
    market_value: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class Concentration:
    weights: tuple[PositionWeight, ...]
    largest: Decimal | None
    top_three: Decimal | None
    hhi: Decimal | None
    unavailable_assets: tuple[str, ...] = ()
    reason: str = ""


def concentration(value: PortfolioValuation) -> Concentration:
    unavailable = tuple(
        p.position.asset.symbol
        for p in value.positions
        if p.market_value is None or p.quote is None or p.quote.currency != "BRL"
    )
    total = value.current_market_value
    if not value.complete or total is None or total <= 0:
        return Concentration(
            (),
            None,
            None,
            None,
            unavailable,
            "Valuation BRL completo e valor aberto positivo são necessários.",
        )
    with localcontext(
        financial_context(
            [total] + [p.market_value for p in value.positions],
            count=len(value.positions),
        )
    ):
        weights = tuple(
            sorted(
                (
                    PositionWeight(
                        p.position.asset, p.market_value, p.market_value / total
                    )
                    for p in value.positions
                    if p.market_value is not None
                ),
                key=lambda item: (-item.weight, item.asset.symbol),
            )
        )
        return Concentration(
            weights,
            weights[0].weight,
            sum((p.weight for p in weights[:3]), Decimal(0)),
            sum((p.weight**2 for p in weights), Decimal(0)),
        )
