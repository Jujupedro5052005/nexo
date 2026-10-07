from datetime import date
from decimal import Decimal

import pytest
from analytics_helpers import analytics_trade
from sqlalchemy import inspect

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import GetAssetHistory, GetAssetQuote
from nexo.domain.enums.transaction_type import TransactionType
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.market_data_provider import MarketDataUnavailableError
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.cache import CachedMarketDataProvider

A, B = Asset("PETR4"), Asset("VALE3")
TODAY = date(2026, 10, 6)


def test_analysis_real_contract_and_explicit_premise(analytics_provider):
    case = AnalyzeAsset(analytics_provider, analytics_provider, today=lambda: TODAY)
    result = case.execute(A, required_yield=Decimal("0.06"))
    assert result.quote.price == 80 and result.annual_dividend == 6
    assert result.bazin.price == 100 and result.bazin.margin.ratio == Decimal("0.2")
    assert result.graham.price**2 == Decimal(1800)
    assert result.risk.max_drawdown == Decimal("-0.25")
    assert len(result.indicators) == 10 and not result.issues
    assert analytics_provider.div_calls == [(A, date(2025, 10, 7), TODAY)]
    jcp = case.execute(A, required_yield=Decimal("0.08"), include_jcp=True)
    assert jcp.annual_dividend == 8 and jcp.bazin.price == 100


def test_bazin_has_no_default_and_invalid_yield_is_rejected_before_network(
    analytics_provider,
):
    case = AnalyzeAsset(analytics_provider, analytics_provider, today=lambda: TODAY)
    assert case.execute(A).bazin.price is None
    analytics_provider.calls.clear()
    with pytest.raises(DomainValidationError):
        case.execute(A, required_yield=Decimal(0))
    assert analytics_provider.calls == []


@pytest.mark.parametrize("section", ["market", "fund", "div", "history"])
def test_partial_failure_preserves_other_sections(analytics_provider, section):
    setattr(
        analytics_provider, section + "_error", MarketDataUnavailableError("offline")
    )
    result = AnalyzeAsset(
        analytics_provider, analytics_provider, today=lambda: TODAY
    ).execute(A, required_yield=Decimal("0.06"))
    assert result.issues
    if section == "market":
        assert (
            result.quote is None
            and result.graham.price is not None
            and result.graham.margin is None
        )
    elif section == "fund":
        assert (
            result.fundamentals is None
            and result.graham.price is None
            and result.bazin.price == 100
        )
    elif section == "div":
        assert (
            result.annual_dividend is None
            and result.bazin.price is None
            and result.graham.price is not None
        )
    else:
        assert (
            result.history is None
            and result.risk.max_drawdown is None
            and result.bazin.price == 100
        )


def test_foreign_quote_has_no_fictitious_brl_margins_or_multiples(analytics_provider):
    analytics_provider.currency = "USD"
    result = AnalyzeAsset(
        analytics_provider, analytics_provider, today=lambda: TODAY
    ).execute(A, required_yield=Decimal("0.06"))
    assert result.bazin.price == 100 and result.bazin.margin is None
    assert result.graham.margin is None
    assert all(
        i.value is None for i in result.indicators if i.key in {"pe", "pb", "dy"}
    )


def test_asset_views_share_cache_and_refresh_all_analytic_keys(analytics_provider):
    cache = CachedMarketDataProvider(analytics_provider, analytics_provider)
    case = AnalyzeAsset(cache, cache, today=lambda: TODAY)
    GetAssetQuote(cache).execute(A)
    GetAssetHistory(cache).execute(A)
    case.execute(A)
    case.execute(A, required_yield=Decimal("0.06"))
    assert (
        len(analytics_provider.calls)
        == len(analytics_provider.history_calls)
        == len(analytics_provider.fund_calls)
        == len(analytics_provider.div_calls)
        == 1
    )
    analytics_provider.prices[A.symbol] = Decimal(90)
    assert case.execute(A, refresh=True).quote.price == 90
    assert len(analytics_provider.calls) == len(analytics_provider.fund_calls) == 2


def test_compare_identical_names_by_id_with_ledger_realized_and_shared_batch(
    analytics_database, analytics_provider
):
    ids, register, comparing, _, _, engine = analytics_database
    register.execute(analytics_trade(ids[0]))
    register.execute(
        analytics_trade(
            ids[0], quantity="2", price="50", kind=TransactionType.SELL, hour=11
        )
    )
    register.execute(analytics_trade(ids[1], quantity="5"))
    register.execute(analytics_trade(ids[1], symbol="VALE3", quantity="10", price="20"))
    result = comparing.execute(ids[:2])
    assert [p.name for p in result] == ["Igual", "Igual"]
    assert [p.portfolio_id for p in result] == list(ids[:2])
    first, second = (p.valuation for p in result)
    assert (
        first.invested_cost,
        first.current_market_value,
        first.realized_profit_loss,
        first.unrealized_profit_loss,
        first.total_profit_loss,
    ) == (240, 640, 40, 400, 440)
    assert second.current_market_value == 800 and second.concentration.hhi == Decimal(
        "0.50"
    )
    assert first.concentration.largest == 1 and second.concentration.top_three == 1
    assert [p.transactions_count for p in result] == [2, 2]
    assert analytics_provider.calls == [(A, B)]
    assert set(inspect(engine).get_table_names()) == {"portfolios", "transactions"}


def test_comparison_partial_and_foreign_are_not_zero_or_normalized(
    analytics_database, analytics_provider
):
    ids, register, comparing, _, cache, _ = analytics_database
    register.execute(analytics_trade(ids[0]))
    register.execute(analytics_trade(ids[0], symbol="ABEV3", quantity="1"))
    partial, empty = comparing.execute((ids[0], ids[2]))
    assert (
        partial.valuation.current_market_value is None
        and partial.valuation.invested_cost == 330
    )
    assert partial.valuation.concentration.weights == ()
    assert partial.valuation.concentration.unavailable_assets == ("ABEV3",)
    assert (
        empty.valuation.current_market_value == 0
        and empty.valuation.concentration.hhi is None
    )
    analytics_provider.currency = "USD"
    cache.invalidate()
    foreign = comparing.execute((ids[0], ids[2]))[0].valuation
    assert foreign.current_market_value is None and any(
        p.market_value is not None for p in foreign.positions
    )
    assert "PETR4" in foreign.concentration.unavailable_assets


@pytest.mark.parametrize("selection", [(1,), (1, 1), (True, 2), (0, 2), (1, 999)])
def test_comparison_rejects_invalid_ids(analytics_database, selection):
    with pytest.raises(DomainValidationError):
        analytics_database[2].execute(selection)


def test_ledger_and_comparison_cost_survive_total_market_failure(
    analytics_database, analytics_provider
):
    ids, register, comparing, _, _, _ = analytics_database
    analytics_provider.market_error = MarketDataUnavailableError("offline")
    register.execute(analytics_trade(ids[0]))
    register.execute(analytics_trade(ids[1], symbol="VALE3"))
    result = comparing.execute(ids[:2])
    assert all(p.valuation.invested_cost == 300 for p in result)
    assert all(p.valuation.current_market_value is None for p in result)
