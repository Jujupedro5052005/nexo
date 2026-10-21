import itertools
from bisect import bisect_right
from dataclasses import dataclass, replace
from datetime import date as Date
from datetime import timedelta
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import PriceHistory
from nexo.domain.models.portfolio_event import PortfolioEvent, PortfolioEventType
from nexo.domain.models.transaction import Transaction
from nexo.domain.reconstruction import rebuild_positions
from nexo.domain.services.cash_ledger import cash_state


@dataclass(frozen=True)
class EquityPoint:
    date: Date
    cash: Decimal
    securities: Decimal
    equity: Decimal
    external_flow: Decimal
    oldest_price_date: Date | None


@dataclass(frozen=True)
class PortfolioPerformance:
    points: tuple[EquityPoint, ...]
    twr: Decimal | None
    issues: tuple[str, ...]
    convention: str = "TWR diário por convenção de fluxos no fim do dia; aproximação para fluxos intradiários. Fechamentos sem reinvestimento automático de proventos."
    sources: tuple[str, ...] = ()


def _portfolio_performance(
    trades: list[Transaction],
    events: tuple[PortfolioEvent, ...],
    histories: dict[Asset, PriceHistory],
    end: Date,
) -> PortfolioPerformance:
    state = cash_state(trades, events)
    if state.opened_at is None:
        return PortfolioPerformance(
            (), None, ("Inicialize o caixa; compras não serão inferidas como aportes.",)
        )
    start = state.opened_at.date()
    if end < start or (end - start).days > 7305:
        return PortfolioPerformance(
            (), None, ("Período inválido ou superior a vinte anos.",)
        )
    issues: list[str] = []
    points = []
    dates = {
        asset: [p.timestamp.date() for p in h.points] for asset, h in histories.items()
    }
    split_checks: dict[tuple[Asset, Date], bool] = {}
    # Ignore future snapshots. Original share units are reconstructed only when
    # the provider explicitly declares how its historical prices treat splits.
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        daily_trades = [t for t in trades if t.occurred_at.date() <= day]
        daily_events = tuple(e for e in events if e.occurred_at.date() <= day)
        cash = cash_state(daily_trades, daily_events).balance
        if cash is None:
            continue
        positions = rebuild_positions(daily_trades, daily_events)
        values: list[Decimal] = []
        price_dates = []
        valid = True
        for position in positions.positions:
            history = histories.get(position.asset)
            index = bisect_right(dates.get(position.asset, []), day) - 1
            available = [history.points[index]] if history and index >= 0 else []
            if not available or (day - available[-1].timestamp.date()).days > 7:
                issues.append(
                    f"{day}: sem fechamento BRL utilizável para {position.asset.symbol} (máximo 7 dias)."
                )
                valid = False
                continue
            assert history is not None
            p = available[-1]
            factor = Decimal(1)
            if history.split_adjusted is True:
                for ex_at, ratio in history.splits:
                    if ex_at.date() > day:
                        factor *= ratio
            elif any(
                e.kind == PortfolioEventType.SPLIT and e.asset == position.asset
                for e in events
            ):
                issues.append(
                    f"{position.asset.symbol}: base de ajuste de splits desconhecida."
                )
                valid = False
            # Any split while held must appear in the user's event ledger.
            for ex_at, ratio in history.splits:
                if start <= ex_at.date() <= day:
                    key = position.asset, ex_at.date()
                    if key not in split_checks:
                        held_before = rebuild_positions(
                            [t for t in trades if t.occurred_at.date() < ex_at.date()],
                            tuple(
                                e for e in events if e.occurred_at.date() < ex_at.date()
                            ),
                        )
                        held = any(
                            p.asset == position.asset for p in held_before.positions
                        )
                        recorded = any(
                            e.kind == PortfolioEventType.SPLIT
                            and e.asset == position.asset
                            and e.occurred_at.date() == ex_at.date()
                            and e.ratio == ratio
                            for e in events
                        )
                        split_checks[key] = held and not recorded
                    if split_checks[key]:
                        issues.append(
                            f"{position.asset.symbol}: split {ex_at.date()} razão {ratio} precisa de registro confirmado."
                        )
                        valid = False
            values.append(position.quantity * p.close * factor)
            price_dates.append(p.timestamp.date())
        if not valid:
            continue
        with localcontext(financial_context([cash, *values], count=len(values))):
            securities = sum(values, Decimal(0))
            external = sum(
                (e.external_flow for e in daily_events if e.occurred_at.date() == day),
                Decimal(0),
            )
            points.append(
                EquityPoint(
                    day,
                    cash,
                    securities,
                    cash + securities,
                    external,
                    min(price_dates) if price_dates else None,
                )
            )
    twr = None
    if not issues and len(points) >= 2:
        with localcontext(
            financial_context([p.equity for p in points], count=len(points))
        ):
            factor = Decimal(1)
            active = False
            for before, after in itertools.pairwise(points):
                if before.equity > 0:
                    factor *= (after.equity - after.external_flow) / before.equity
                    active = True
                elif after.equity != after.external_flow:
                    issues.append(
                        "Retorno sem denominador positivo após período sem capital."
                    )
                    break
            if active and not issues:
                twr = factor - 1
    if len(points) < 2:
        issues.append(
            "São necessários dois fechamentos de patrimônio para calcular TWR."
        )
    return PortfolioPerformance(tuple(points), twr, tuple(dict.fromkeys(issues))[:30])


def portfolio_performance(
    trades: list[Transaction],
    events: tuple[PortfolioEvent, ...],
    histories: dict[Asset, PriceHistory],
    end: Date,
) -> PortfolioPerformance:
    values = (
        [v for t in trades for v in (t.quantity, t.unit_price, t.fees)]
        + [v for e in events for v in (e.amount, e.withholding, e.ratio or Decimal(1))]
        + [p.close for h in histories.values() for p in h.points]
    )
    with localcontext(financial_context(values, count=7305)):
        result = _portfolio_performance(trades, events, histories, end)
        sources = tuple(
            f"{asset.symbol}: {h.source} • consultado {h.retrieved_at.isoformat()} • ajuste de splits: {h.split_adjusted}"
            for asset, h in histories.items()
        )
        return replace(result, sources=sources)
