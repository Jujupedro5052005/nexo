from dataclasses import dataclass

from nexo.domain.interfaces.market_data_provider import MarketDataError
from nexo.domain.interfaces.official_data_provider import (
    OfficialCompanyDataProvider,
    OfficialFinancialStatementProvider,
)
from nexo.domain.models.asset import Asset
from nexo.domain.models.official_data import OfficialCompany, OfficialFinancialStatement


@dataclass(frozen=True, slots=True)
class OfficialCompanyData:
    company: OfficialCompany | None
    statements: tuple[OfficialFinancialStatement, ...]
    issues: tuple[str, ...]


class GetOfficialCompanyData:
    def __init__(
        self,
        companies: OfficialCompanyDataProvider,
        statements: OfficialFinancialStatementProvider,
    ) -> None:
        self.companies, self.statements = companies, statements

    def execute(self, asset: Asset) -> OfficialCompanyData:
        company = None
        rows: tuple[OfficialFinancialStatement, ...] = ()
        issues = []
        try:
            company = self.companies.get_company(asset)
            rows = self.statements.get_statements(asset)
        except MarketDataError as error:
            issues.append(str(error))
        return OfficialCompanyData(company, rows, tuple(issues))

    def invalidate(self, asset: Asset) -> None:
        self.statements.invalidate(asset)
