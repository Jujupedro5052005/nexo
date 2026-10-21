from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.domain.models.transaction import Transaction


class InsufficientCashError(DomainValidationError):
    pass


@dataclass(frozen=True)
class CashState:
    balance: Decimal | None
    opened_at: datetime | None
    deposits: Decimal
    withdrawals: Decimal
    income: Decimal
    costs: Decimal


def _cash_state(
    trades: list[Transaction], events: tuple[PortfolioEvent, ...]
) -> CashState:
    openings = [e for e in events if e.kind == PortfolioEventType.OPENING]
    if len(openings) > 1:
        raise DomainValidationError("Caixa já inicializado; use aporte ou retirada.")
    all_times = [t.occurred_at for t in trades] + [e.occurred_at for e in events]
    if len({t.utcoffset() is not None for t in all_times}) > 1:
        raise DomainValidationError("Não misture datas com e sem fuso horário.")
    if not openings:
        if any(e.kind != PortfolioEventType.SPLIT for e in events):
            raise DomainValidationError(
                "Inicialize o saldo de caixa antes de registrar fluxos."
            )
        return CashState(None, None, Decimal(0), Decimal(0), Decimal(0), Decimal(0))
    opening = openings[0]
    if any(
        e.occurred_at < opening.occurred_at and e.kind != PortfolioEventType.SPLIT
        for e in events
    ):
        raise DomainValidationError("Evento de caixa anterior à inicialização.")
    # At equal times: opening, receipts, trades, then standalone payments.
    rows: list[tuple[datetime, int, int, Decimal]] = []
    for e in events:
        if e.kind == PortfolioEventType.SPLIT:
            continue
        priority = (
            0 if e.kind == PortfolioEventType.OPENING else 3 if e.cash_effect < 0 else 1
        )
        rows.append((e.occurred_at, priority, e.id or 2**63, e.cash_effect))
    for t in trades:
        if t.occurred_at >= opening.occurred_at:
            rows.append(
                (
                    t.occurred_at,
                    2,
                    t.id or 2**63,
                    t.amounts()[1].copy_negate()
                    if t.transaction_type == TransactionType.BUY
                    else t.amounts()[1],
                )
            )
    with localcontext(financial_context([r[3] for r in rows], count=len(rows))):
        balance = Decimal(0)
        for at, _priority, _identity, effect in sorted(rows, key=lambda r: r[:3]):
            balance += effect
            if balance < 0:
                raise InsufficientCashError(
                    f"Caixa insuficiente em {at.isoformat(sep=' ')}. Faltam R$ {-balance:.2f}. Registre o aporte efetivamente realizado ou corrija os valores/data."
                )
        return CashState(
            balance,
            opening.occurred_at,
            sum(
                (e.amount for e in events if e.kind == PortfolioEventType.DEPOSIT),
                Decimal(0),
            ),
            sum(
                (e.amount for e in events if e.kind == PortfolioEventType.WITHDRAWAL),
                Decimal(0),
            ),
            sum(
                (
                    e.cash_effect
                    for e in events
                    if e.kind in {PortfolioEventType.DIVIDEND, PortfolioEventType.JCP}
                ),
                Decimal(0),
            ),
            sum(
                (
                    e.amount
                    for e in events
                    if e.kind in {PortfolioEventType.FEE, PortfolioEventType.TAX}
                ),
                Decimal(0),
            )
            + sum((e.withholding for e in events), Decimal(0))
            + sum(
                (t.fees for t in trades if t.occurred_at >= opening.occurred_at),
                Decimal(0),
            ),
        )


def cash_state(
    trades: list[Transaction], events: tuple[PortfolioEvent, ...]
) -> CashState:
    if len({t.portfolio_id for t in trades} | {e.portfolio_id for e in events}) > 1:
        raise DomainValidationError(
            "O caixa deve ser reconstruído para uma carteira por vez."
        )
    values = [v for t in trades for v in (t.quantity, t.unit_price, t.fees)] + [
        v for e in events for v in (e.amount, e.withholding)
    ]
    with localcontext(financial_context(values, count=len(trades) + len(events))):
        return _cash_state(trades, events)
