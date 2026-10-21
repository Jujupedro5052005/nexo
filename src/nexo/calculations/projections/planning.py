from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal


@dataclass(frozen=True)
class BudgetSummary:
    income: Decimal
    fixed: Decimal
    variable: Decimal
    available: Decimal


def monthly_budget(entries: tuple[BudgetEntry, ...], month: date) -> BudgetSummary:
    selected = [
        e for e in entries if (e.month.year, e.month.month) == (month.year, month.month)
    ]
    with localcontext(
        financial_context([e.amount for e in selected], count=len(selected))
    ):
        values = {
            kind: sum((e.amount for e in selected if e.kind == kind), Decimal(0))
            for kind in ("income", "fixed", "variable")
        }
        return BudgetSummary(
            values["income"],
            values["fixed"],
            values["variable"],
            values["income"] - values["fixed"] - values["variable"],
        )


def goal_projection(goal: FinancialGoal, today: date) -> tuple[Decimal, Decimal | None]:
    with localcontext(financial_context([goal.current, goal.target])):
        progress = min(Decimal(1), goal.current / goal.target)
        remaining = max(Decimal(0), goal.target - goal.current)
        if not remaining:
            return progress, Decimal(0)
        if goal.deadline < today:
            return progress, None
        months = max(
            1,
            (goal.deadline.year - today.year) * 12 + goal.deadline.month - today.month,
        )
        return progress, remaining / months
