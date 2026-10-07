from abc import ABC, abstractmethod

from nexo.domain.models.asset import Asset
from nexo.domain.models.official_data import OfficialCompany, OfficialFinancialStatement


class OfficialCompanyDataProvider(ABC):
    @abstractmethod
    def get_company(self, asset: Asset) -> OfficialCompany:
        """Resolve exact official identity; never match company names heuristically."""


class OfficialFinancialStatementProvider(ABC):
    def invalidate(self, asset: Asset) -> None:
        """Discard normalized results for an explicit retry, preserving valid datasets."""

    @abstractmethod
    def get_statements(self, asset: Asset) -> tuple[OfficialFinancialStatement, ...]:
        """Most recent official reports, consolidated preferred."""
