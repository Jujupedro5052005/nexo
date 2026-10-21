import itertools
from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.errors import DomainValidationError


def valid_rate(rate: Decimal) -> None:
    if not rate.is_finite() or rate <= -1:
        raise DomainValidationError(
            "Taxa deve ser finita e superior a −100% por período."
        )


def future_value(
    initial: Decimal, payment: Decimal, rate: Decimal, periods: int
) -> Decimal:
    valid_rate(rate)
    if (
        not initial.is_finite()
        or not payment.is_finite()
        or initial < 0
        or payment < 0
        or type(periods) is not int
        or not 0 <= periods <= 1200
    ):
        raise DomainValidationError(
            "Capital/aporte não negativos e prazo de até 1200 períodos."
        )
    with localcontext(financial_context([initial, payment, rate])):
        growth = (1 + rate) ** periods
        return initial * growth + payment * ((growth - 1) / rate if rate else periods)


def required_payment(
    target: Decimal, initial: Decimal, rate: Decimal, periods: int
) -> Decimal:
    valid_rate(rate)
    if (
        not target.is_finite()
        or not initial.is_finite()
        or target < 0
        or initial < 0
        or type(periods) is not int
        or not 1 <= periods <= 1200
    ):
        raise DomainValidationError(
            "Objetivo/capital não negativos e prazo positivo até 1200 períodos."
        )
    with localcontext(financial_context([target, initial, rate])):
        factor = ((1 + rate) ** periods - 1) / rate if rate else Decimal(periods)
        return max(Decimal(0), (target - initial * (1 + rate) ** periods) / factor)


def real_rate(nominal: Decimal, inflation: Decimal) -> Decimal:
    valid_rate(nominal)
    valid_rate(inflation)
    return (1 + nominal) / (1 + inflation) - 1


def npv(flows: tuple[Decimal, ...], rate: Decimal) -> Decimal:
    valid_rate(rate)
    if not flows or len(flows) > 1201 or any(not f.is_finite() for f in flows):
        raise DomainValidationError(
            "Informe até 1201 fluxos periódicos, incluindo investimento inicial negativo."
        )
    with localcontext(financial_context([rate, *flows], count=len(flows))):
        return sum((flow / (1 + rate) ** i for i, flow in enumerate(flows)), Decimal(0))


def irr(flows: tuple[Decimal, ...]) -> Decimal:
    nonzero = [f for f in flows if f]
    changes = sum((a > 0) != (b > 0) for a, b in itertools.pairwise(nonzero))
    if len(nonzero) < 2 or changes != 1:
        raise DomainValidationError(
            "TIR exige uma única mudança de sinal; múltiplas TIRs exigem análise pelo VPL."
        )
    low, high = Decimal("-.9999"), Decimal(1)
    while npv(flows, low) * npv(flows, high) > 0 and high < 1000000:
        high *= 2
    if npv(flows, low) * npv(flows, high) > 0:
        raise DomainValidationError(
            "Não foi possível delimitar uma TIR no intervalo de busca."
        )
    with localcontext(financial_context(flows, count=len(flows))):
        for _ in range(180):
            mid = (low + high) / 2
            value = npv(flows, mid)
            if abs(value) < Decimal("1e-24"):
                return mid
            if npv(flows, low) * value > 0:
                low = mid
            else:
                high = mid
        return (low + high) / 2


@dataclass(frozen=True)
class DebtPayment:
    period: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal


def amortization(
    principal: Decimal, rate: Decimal, periods: int, system: str
) -> tuple[DebtPayment, ...]:
    if (
        not rate.is_finite()
        or rate < 0
        or not principal.is_finite()
        or principal <= 0
        or not 1 <= periods <= 600
        or system not in {"PRICE", "SAC"}
    ):
        raise DomainValidationError(
            "Dívida positiva, juros não negativos, 1–600 parcelas e sistema PRICE/SAC."
        )
    with localcontext(financial_context([principal, rate])):
        balance = principal
        fixed = (
            principal / periods
            if rate == 0
            else principal * rate / (1 - (1 + rate) ** (-periods))
        )
        rows = []
        for i in range(1, periods + 1):
            interest = balance * rate
            repayment = (
                (fixed - interest if system == "PRICE" else principal / periods)
                if i < periods
                else balance
            )
            balance -= repayment
            rows.append(
                DebtPayment(i, repayment + interest, interest, repayment, balance)
            )
        return tuple(rows)


def discounted_company(
    cashflows: tuple[Decimal, ...],
    discount: Decimal,
    growth: Decimal,
    net_debt: Decimal,
    shares: Decimal,
) -> Decimal:
    valid_rate(discount)
    valid_rate(growth)
    if (
        not shares.is_finite()
        or not net_debt.is_finite()
        or any(not c.is_finite() for c in cashflows)
        or discount <= growth
        or shares <= 0
        or not cashflows
        or len(cashflows) > 100
    ):
        raise DomainValidationError(
            "FCD exige taxa > crescimento terminal, ações positivas e até 100 fluxos operacionais."
        )
    with localcontext(
        financial_context([*cashflows, discount, growth, net_debt, shares])
    ):
        enterprise = sum(
            (c / (1 + discount) ** (i + 1) for i, c in enumerate(cashflows)), Decimal(0)
        )
        terminal = (
            cashflows[-1]
            * (1 + growth)
            / (discount - growth)
            / (1 + discount) ** len(cashflows)
        )
        return (enterprise + terminal - net_debt) / shares


def bond_metrics(
    face: Decimal, coupon: Decimal, yield_rate: Decimal, periods: int
) -> tuple[Decimal, Decimal, Decimal]:
    valid_rate(yield_rate)
    if (
        not face.is_finite()
        or not coupon.is_finite()
        or face <= 0
        or coupon < 0
        or type(periods) is not int
        or not 1 <= periods <= 600
    ):
        raise DomainValidationError(
            "Título exige valor nominal positivo, cupom não negativo e 1–600 períodos."
        )
    with localcontext(financial_context([face, coupon, yield_rate])):
        flows = [
            coupon + face if i == periods else coupon for i in range(1, periods + 1)
        ]
        price = sum(
            (v / (1 + yield_rate) ** i for i, v in enumerate(flows, 1)), Decimal(0)
        )
        duration = (
            sum(
                (i * v / (1 + yield_rate) ** i for i, v in enumerate(flows, 1)),
                Decimal(0),
            )
            / price
        )
        return price, duration, duration / (1 + yield_rate)
