from abc import ABC, abstractmethod
from datetime import date

from nexo.domain.models.asset import Asset
from nexo.domain.models.fundamentals import CompanyFundamentals, DividendSummary


class FundamentalDataProvider(ABC):
    """Company inputs and cash distributions; not a ledger of received income."""

    @abstractmethod
    def get_fundamentals(self, asset: Asset) -> CompanyFundamentals:
        """Return current company inputs with availability/source metadata."""

    def get_dividends(
        self, asset: Asset, start_date: date, end_date: date
    ) -> DividendSummary:
        """Return distributions in the inclusive payment-date window."""
        raise NotImplementedError("Inject a separate DividendDataProvider.")
