"""Pearson correlation over aligned close-to-close returns; no gap filling."""

from collections.abc import Mapping
from decimal import Decimal, localcontext
from itertools import pairwise


def aligned_correlation(
    left: Mapping[str, Decimal],
    right: Mapping[str, Decimal],
    *,
    minimum_returns: int = 20,
) -> Decimal | None:
    if minimum_returns < 2:
        raise ValueError("Pelo menos dois retornos necessários.")
    dates = sorted(set(left) & set(right))
    # Only intervals consecutive in both original series are compared. A missing
    # observation must not become a zero return or a multi-day 'daily' return.
    left_dates, right_dates = sorted(left), sorted(right)
    left_pairs = set(pairwise(left_dates))
    right_pairs = set(pairwise(right_dates))
    pairs = [
        (a, b)
        for a, b in pairwise(dates)
        if (a, b) in left_pairs and (a, b) in right_pairs
    ]
    if len(pairs) < minimum_returns or any(
        not v.is_finite() or v <= 0 for v in (*left.values(), *right.values())
    ):
        return None
    with localcontext() as context:
        context.prec = 50
        x = [left[b] / left[a] - 1 for a, b in pairs]
        y = [right[b] / right[a] - 1 for a, b in pairs]
        mx, my = sum(x, Decimal(0)) / len(x), sum(y, Decimal(0)) / len(y)
        cross = sum(
            ((a - mx) * (b - my) for a, b in zip(x, y, strict=True)), Decimal(0)
        )
        sx, sy = (
            sum(((a - mx) ** 2 for a in x), Decimal(0)),
            sum(((b - my) ** 2 for b in y), Decimal(0)),
        )
        if not sx or not sy:
            return None
        return max(Decimal(-1), min(Decimal(1), cross / (sx * sy).sqrt()))
