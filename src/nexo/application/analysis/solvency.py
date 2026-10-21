from decimal import Decimal

from nexo.calculations.indicators.insolvency import SolvencyResult, insolvency_scores


class EvaluateSolvency:
    """Evaluate explicitly reconciled manual accounts; never infer missing data."""

    def execute(
        self, values: dict[str, Decimal], *, nonfinancial: bool, aligned: bool
    ) -> tuple[SolvencyResult, ...]:
        return insolvency_scores(values, nonfinancial=nonfinancial, aligned=aligned)
