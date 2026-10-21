from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, localcontext
from math import exp, pi, sqrt
from statistics import NormalDist

from nexo.calculations.precision import financial_context
from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True)
class TailRisk:
    observations: int
    confidence: Decimal
    horizon: int
    historical_var: Decimal
    historical_es: Decimal
    normal_var: Decimal
    normal_es: Decimal
    volatility: Decimal


def tail_risk(
    returns: tuple[Decimal, ...],
    exposure: Decimal,
    confidence: Decimal = Decimal(".95"),
    horizon: int = 1,
) -> TailRisk:
    if (
        not exposure.is_finite()
        or exposure <= 0
        or not confidence.is_finite()
        or not Decimal(".5") < confidence < 1
    ):
        raise DomainValidationError(
            "Exposição positiva e confiança entre 50% e 100% são necessárias."
        )
    if (
        type(horizon) is not int
        or not 1 <= horizon <= 252
        or len(returns) < horizon + 19
    ):
        raise DomainValidationError(
            "São necessárias pelo menos vinte janelas completas; horizonte de 1 a 252 pregões."
        )
    if any(not r.is_finite() or r < -1 for r in returns):
        raise DomainValidationError(
            "Retornos simples devem ser finitos e não inferiores a −100%."
        )
    with localcontext(
        financial_context([exposure, confidence, *returns], count=len(returns))
    ):
        windows = []
        for index in range(len(returns) - horizon + 1):
            growth = Decimal(1)
            for r in returns[index : index + horizon]:
                growth *= 1 + r
            windows.append(1 - growth)
        losses = sorted(windows)
        rank = (
            int((confidence * len(losses)).to_integral_value(rounding=ROUND_CEILING))
            - 1
        )
        threshold = losses[rank]
        tail = [loss for loss in losses if loss >= threshold]
        mean = sum(returns, Decimal(0)) / len(returns)
        sigma = (
            sum(((r - mean) ** 2 for r in returns), Decimal(0)) / (len(returns) - 1)
        ).sqrt()
        z = NormalDist().inv_cdf(float(confidence))
        phi = Decimal(str(exp(-z * z / 2) / sqrt(2 * pi)))
        scaled_sigma = sigma * Decimal(horizon).sqrt()
        return TailRisk(
            len(returns),
            confidence,
            horizon,
            max(Decimal(0), threshold) * exposure,
            max(Decimal(0), sum(tail, Decimal(0)) / len(tail)) * exposure,
            max(Decimal(0), Decimal(str(z)) * scaled_sigma - mean * horizon) * exposure,
            max(Decimal(0), phi / (1 - confidence) * scaled_sigma - mean * horizon)
            * exposure,
            sigma,
        )


def covariance(x: tuple[Decimal, ...], y: tuple[Decimal, ...]) -> Decimal:
    if len(x) != len(y) or len(x) < 2 or any(not v.is_finite() for v in (*x, *y)):
        raise DomainValidationError(
            "Séries alinhadas com pelo menos dois retornos são necessárias."
        )
    with localcontext(financial_context([*x, *y], count=len(x))):
        mx, my = sum(x, Decimal(0)) / len(x), sum(y, Decimal(0)) / len(y)
        return sum(((a - mx) * (b - my) for a, b in zip(x, y)), Decimal(0)) / (
            len(x) - 1
        )


def comparative_risk(
    x: tuple[Decimal, ...], benchmark: tuple[Decimal, ...], annual_rf: Decimal
) -> dict[str, Decimal | None]:
    if not annual_rf.is_finite() or annual_rf <= -1:
        raise DomainValidationError(
            "Taxa livre de risco deve ser superior a −100% a.a."
        )
    with localcontext(financial_context([*x, *benchmark, annual_rf], count=len(x))):
        vx, vb = covariance(x, x), covariance(benchmark, benchmark)
        cov = covariance(x, benchmark)
        daily_rf = (1 + annual_rf) ** (Decimal(1) / 252) - 1
        excess = sum(x, Decimal(0)) / len(x) - daily_rf
        beta = cov / vb if vb > 0 else None
        return {
            "beta": beta,
            "correlation": cov / (vx * vb).sqrt() if vx > 0 and vb > 0 else None,
            "sharpe": excess / vx.sqrt() * Decimal(252).sqrt() if vx > 0 else None,
            "treynor": excess * 252 / beta if beta is not None and beta != 0 else None,
        }
