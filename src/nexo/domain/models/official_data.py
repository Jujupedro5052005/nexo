from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CompanyIdentity:
    ticker_primary: str
    queried_ticker: str
    tickers: tuple[str, ...]
    corporate_name: str
    trade_name: str
    cvm_code: str
    cnpj: str
    sector: str = ""
    status: str = ""
    source: str = "bolsai"


@dataclass(frozen=True, slots=True)
class OfficialCompany:
    cnpj: str
    cvm_code: str
    corporate_name: str
    trade_name: str
    status: str
    category: str
    registration_date: date | None
    source: str = "CVM"


@dataclass(frozen=True, slots=True)
class OfficialFinancialStatement:
    cvm_code: str
    cnpj: str
    reference_date: date
    report_type: str
    statement_type: str
    account_code: str
    account_name: str
    value: Decimal
    consolidated: bool
    source: str = "CVM"
    period_start: date | None = None
    period_end: date | None = None
    version: int = 1


@dataclass(frozen=True, slots=True)
class CorporateAction:
    asset_symbol: str
    ex_date: date
    split_ratio: Decimal
    source: str
