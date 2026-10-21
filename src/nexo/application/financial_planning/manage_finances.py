from dataclasses import replace
from datetime import datetime, timezone

from nexo.domain.interfaces.market_data_provider import MarketDataProvider
from nexo.domain.interfaces.personal_finance_repository import PersonalFinanceRepository
from nexo.domain.models.asset import Asset
from nexo.domain.models.personal_finance import BudgetEntry, FinancialGoal, PriceAlert


class ManageFinances:
    """Local planning data is independent of the investment ledger."""

    def __init__(
        self, repository: PersonalFinanceRepository, market: MarketDataProvider
    ) -> None:
        self.repository, self.market = repository, market

    def budget_entries(self) -> tuple[BudgetEntry, ...]:
        return self.repository.budget_entries()

    def save_budget(self, entry: BudgetEntry) -> None:
        self.repository.save_budget(entry)

    def goals(self) -> tuple[FinancialGoal, ...]:
        return self.repository.goals()

    def save_goal(self, goal: FinancialGoal) -> None:
        self.repository.save_goal(goal)

    def alerts(self) -> tuple[PriceAlert, ...]:
        return self.repository.alerts()

    def save_alert(self, alert: PriceAlert) -> None:
        self.repository.save_alert(alert)

    def check_alerts(self) -> None:
        alerts = self.repository.alerts()
        active = [a for a in alerts if a.enabled]
        with self.market.refresh_context(True):
            batch = self.market.get_quotes(Asset(a.symbol) for a in active)
        quotes = {q.asset.symbol: q for q in batch.quotes}
        for alert in active:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            quote = quotes.get(alert.symbol)
            if quote is None or quote.currency != "BRL":
                self.repository.save_alert(
                    replace(
                        alert,
                        checked_at=now,
                        state="Cotação BRL indisponível",
                        quote_at="",
                    )
                )
                continue
            matches = (
                quote.price <= alert.threshold
                if alert.direction == "below"
                else quote.price >= alert.threshold
            )
            # Condition is on the returned snapshot, never a claim of a live trade.
            self.repository.save_alert(
                replace(
                    alert,
                    checked_at=now,
                    quote_at=f"{quote.source} • {quote.market_time or 'horário de mercado desconhecido'} • {quote.price}",
                    state="Condição atingida na cotação"
                    if matches
                    else "Aguardando condição",
                    triggered_at=now
                    if matches and alert.state != "Condição atingida na cotação"
                    else alert.triggered_at,
                )
            )
