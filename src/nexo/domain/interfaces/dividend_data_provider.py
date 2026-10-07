from abc import ABC, abstractmethod
from datetime import date

from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import DividendSummary


class DividendDataProvider(ABC):
    @abstractmethod
    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        """Preserve event type, date basis, source and limitations."""
