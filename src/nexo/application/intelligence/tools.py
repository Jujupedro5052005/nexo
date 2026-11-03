"""Read-only, allowlisted financial tools using the existing application services."""

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from nexo.application.assets.market_data import GetAssetHistory, GetAssetQuote
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.calculations.valuation.intelligence import (
    ValuationInputs,
    calculate_valuation,
    sensitivity,
)
from nexo.core.cancellation import OperationCancelled, check_cancelled
from nexo.domain.interfaces.dividend_data_provider import DividendDataProvider
from nexo.domain.interfaces.fundamental_data_provider import FundamentalDataProvider
from nexo.domain.interfaces.intelligence import IntelligenceStorage
from nexo.domain.models.asset import Asset
from nexo.domain.models.intelligence import (
    AnalysisRequest,
    ToolCall,
    ToolResult,
    utc_now,
)


def json_data(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return json_data(asdict(value))
    if isinstance(value, dict):
        return {str(k): json_data(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_data(v) for v in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def encode(value: Any) -> str:
    return json.dumps(json_data(value), ensure_ascii=False, allow_nan=False)


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PortfolioArguments(Arguments):
    portfolio_id: int = Field(gt=0, strict=True)


class TransactionArguments(PortfolioArguments):
    limit: int = Field(default=10, ge=1, le=20, strict=True)


class AssetArguments(Arguments):
    symbol: str = Field(min_length=1, max_length=24, pattern=r"^[A-Za-z0-9.^=_-]+$")


class HistoryArguments(AssetArguments):
    period: Literal["1mo", "3mo", "1y"] = "1mo"


class MethodArguments(Arguments):
    methodology_id: str


class CompareArguments(Arguments):
    symbols: list[str] = Field(min_length=2, max_length=4)


class ValuationArguments(ValuationInputs):
    pass


TOOL_ARGUMENTS: dict[str, type[BaseModel]] = {
    "list_portfolios": Arguments,
    "get_portfolio_snapshot": PortfolioArguments,
    "get_portfolio_positions": PortfolioArguments,
    "get_portfolio_transactions": TransactionArguments,
    "calculate_portfolio_exposure": PortfolioArguments,
    "get_asset_quote": AssetArguments,
    "get_asset_fundamentals": AssetArguments,
    "get_dividend_history": AssetArguments,
    "get_asset_price_history": HistoryArguments,
    "get_methodology": MethodArguments,
    "list_methodologies": Arguments,
    "calculate_valuation": ValuationArguments,
    "compare_assets": CompareArguments,
}


class FinancialTools:
    def __init__(
        self,
        portfolios: ListPortfolios,
        positions: LoadPortfolioPositions,
        valuation: LoadPortfolioValuation,
        quote: GetAssetQuote,
        history: GetAssetHistory,
        fundamentals: FundamentalDataProvider,
        dividends: DividendDataProvider,
        storage: IntelligenceStorage,
        *,
        transactions: ListTransactions | None = None,
    ) -> None:
        self.portfolios, self.positions, self.valuation = (
            portfolios,
            positions,
            valuation,
        )
        self.quote, self.history = quote, history
        self.transactions = transactions
        self.fundamentals, self.dividends, self.storage = (
            fundamentals,
            dividends,
            storage,
        )

    def declarations(self) -> list[dict[str, Any]]:
        # Local calculation inputs come exclusively from the user's explicit premises.
        return [
            {
                "name": name,
                "description": f"Consulta somente leitura: {name}. Preserva None, fontes e datas.",
                "parameters_json_schema": model.model_json_schema(),
            }
            for name, model in TOOL_ARGUMENTS.items()
            if name != "calculate_valuation"
        ]

    def execute(self, call: ToolCall, request: AnalysisRequest) -> ToolResult:
        check_cancelled()
        try:
            if call.name not in TOOL_ARGUMENTS:
                raise ValueError("Ferramenta não permitida.")
            args = TOOL_ARGUMENTS[call.name].model_validate(call.arguments).model_dump()
            if "portfolio_id" in args and args["portfolio_id"] != request.portfolio_id:
                raise ValueError(
                    "Selecione explicitamente a carteira para compartilhar seu resumo."
                )
            if call.name == "list_portfolios":
                # Names and other portfolios are kept local, even when asked by the model.
                data: Any = [
                    {"id": p.id}
                    for p in self.portfolios.execute()
                    if p.id == request.portfolio_id
                ]
            elif call.name == "get_portfolio_positions":
                data = self.positions.execute(args["portfolio_id"])
            elif call.name == "get_portfolio_transactions":
                if self.transactions is None:
                    raise ValueError("Histórico não configurado.")
                history = self.transactions.execute(args["portfolio_id"])
                data = {
                    "transactions": history[-args["limit"] :],
                    "total_count": len(history),
                    "truncated": len(history) > args["limit"],
                    "source": "ledger local",
                }
            elif call.name in {
                "get_portfolio_snapshot",
                "calculate_portfolio_exposure",
            }:
                value = self.valuation.execute(args["portfolio_id"])
                data = (
                    value.concentration
                    if call.name == "calculate_portfolio_exposure"
                    else {
                        "valuation": json_data(value),
                        "concentration": json_data(value.concentration),
                        "source": "ledger reconstruído + providers de mercado",
                        "cash_included": False,
                    }
                )
            elif call.name == "get_asset_quote":
                q = self.quote.execute(Asset(args["symbol"]))
                data = {
                    **json_data(q),
                    "freshness": q.freshness,
                    "age_seconds_at_query": q.data_age_seconds,
                    "unit": "currency_per_share",
                    "availability": "available",
                    "snapshot_age_seconds": max(
                        0, int((utc_now() - q.retrieved_at).total_seconds())
                    ),
                    "stale_snapshot": (utc_now() - q.retrieved_at).total_seconds()
                    > 300,
                }
            elif call.name == "get_asset_fundamentals":
                f = self.fundamentals.get_fundamentals(Asset(args["symbol"]))
                data = {
                    **json_data(f),
                    "availability": "partial" if f.issues else "available",
                    "fiscal_period": f.reference_date.isoformat()
                    if f.reference_date
                    else None,
                    "units": {
                        "eps": "BRL/share",
                        "bvps": "BRL/share",
                        "roe": "fraction",
                    },
                    "stale_snapshot": (utc_now() - f.retrieved_at).total_seconds()
                    > 172800,
                    "missing_fields": [
                        field
                        for field in ("eps", "bvps", "roe", "net_income")
                        if getattr(f, field) is None
                    ],
                }
            elif call.name == "get_asset_price_history":
                data = self.history.execute(Asset(args["symbol"]), args["period"])
            elif call.name == "get_dividend_history":
                end = utc_now().date()
                data = self.dividends.get_dividends(
                    Asset(args["symbol"]), end - timedelta(days=365), end
                )
            elif call.name in {"list_methodologies", "get_methodology"}:
                methods = [
                    m
                    for m in self.storage.methodologies()
                    if m.review_status == "approved"
                ]
                data = (
                    methods
                    if call.name == "list_methodologies"
                    else next(
                        m for m in methods if m.methodology_id == args["methodology_id"]
                    )
                )
            elif call.name == "compare_assets":
                symbols = [AssetArguments(symbol=s).symbol for s in args["symbols"]]
                data = [
                    self.execute(
                        ToolCall(name="get_asset_quote", arguments={"symbol": s}),
                        request,
                    )
                    for s in dict.fromkeys(symbols)
                ]
            else:
                # Approval of text cannot register arbitrary formulas. Only these IDs execute.
                method = next(
                    m
                    for m in self.storage.methodologies()
                    if m.methodology_id == args["method"]
                    and m.review_status == "approved"
                )
                if args["asset_type"] not in method.applicable_asset_types:
                    raise ValueError("Metodologia incompatível.")
                # The model cannot introduce its own financial assumptions.
                expected = {
                    **request.assumptions,
                    "method": request.methodology_id,
                    "asset_type": request.asset_type,
                }
                for key, value in call.arguments.items():
                    if key not in {"quote", "quote_source"} and encode(value) != encode(
                        expected.get(key)
                    ):
                        raise ValueError(
                            "Premissas precisam ser informadas pelo usuário."
                        )
                inputs = ValuationInputs.model_validate(args)
                data = {
                    **calculate_valuation(inputs),
                    "sensitivity": sensitivity(inputs),
                }
            check_cancelled()
            return ToolResult(name=call.name, available=True, data=json_data(data))
        except OperationCancelled:
            raise
        except (ValueError, StopIteration):
            return ToolResult(
                name=call.name,
                available=False,
                error="Argumentos inválidos, metodologia não aprovada/incompatível ou premissas essenciais ausentes. Verifique os campos informados.",
            )
        except Exception:  # noqa: BLE001 - Safe boundary; never expose provider secrets.
            return ToolResult(
                name=call.name,
                available=False,
                error="Dado indisponível: falha do serviço financeiro. Nenhum valor foi substituído por zero.",
            )
