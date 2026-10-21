from typing import Protocol

from nexo.domain.models.portfolio_event import PortfolioEvent


class PortfolioEventRepository(Protocol):
    def list_events(self, portfolio_id: int) -> tuple[PortfolioEvent, ...]: ...
    def add_event(self, event: PortfolioEvent) -> PortfolioEvent: ...
