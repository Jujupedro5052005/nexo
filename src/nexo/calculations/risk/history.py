from dataclasses import dataclass
from decimal import Decimal, localcontext
from itertools import pairwise

from nexo.calculations.precision import financial_context
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.market_data import PriceHistory


@dataclass(frozen=True, slots=True)
class HistoricalRisk:
    observations: int
    daily_volatility: Decimal | None
    annual_volatility: Decimal | None
    max_drawdown: Decimal | None
    trading_days: int
    reason: str = ""


def historical_risk(
    history: PriceHistory | None, *, trading_days: int = 252
) -> HistoricalRisk:
    if type(trading_days) is not int or trading_days <= 0:
        raise DomainValidationError("trading_days must be a positive integer.")
    points = history.points if history else ()
    if len(points) < 2 or any(a.timestamp >= b.timestamp for a, b in pairwise(points)):
        return HistoricalRisk(
            len(points),
            None,
            None,
            None,
            trading_days,
            "São necessários pelo menos dois fechamentos em datas distintas e crescentes.",
        )
    with localcontext(financial_context((p.close for p in points), count=len(points))):
        returns = [b.close / a.close - 1 for a, b in pairwise(points)]
        daily = None
        if len(returns) >= 2:
            mean = sum(returns, Decimal(0)) / len(returns)
            variance = sum(((r - mean) ** 2 for r in returns), Decimal(0)) / (
                len(returns) - 1
            )
            daily = variance.sqrt()
        peak = points[0].close
        drawdown = Decimal(0)
        for point in points:
            peak = max(peak, point.close)
            drawdown = min(drawdown, point.close / peak - 1)
        return HistoricalRisk(
            len(points),
            daily,
            daily * Decimal(trading_days).sqrt() if daily is not None else None,
            drawdown,
            trading_days,
            "Volatilidade amostral exige três fechamentos." if daily is None else "",
        )
