from dataclasses import FrozenInstanceError

import pytest

from nexo.domain.errors import DomainValidationError
from nexo.domain.models.asset import Asset


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("PETR4", "PETR4"),
        ("petr4", "PETR4"),
        (" petr4 ", "PETR4"),
        ("AAPL", "AAPL"),
        ("btc-usd", "BTC-USD"),
        ("brk.b", "BRK.B"),
    ],
)
def test_symbol_normalization(symbol: str, expected: str) -> None:
    assert Asset(symbol).symbol == expected


@pytest.mark.parametrize("symbol", ["", " ", "\t\n", None, 123])
def test_invalid_symbol(symbol) -> None:
    with pytest.raises(DomainValidationError, match="symbol"):
        Asset(symbol)


def test_value_equality_and_hash() -> None:
    assert Asset(" petr4 ") == Asset("PETR4")
    assert len({Asset("petr4"), Asset("PETR4"), Asset("VALE3")}) == 2


def test_asset_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        Asset("PETR4").symbol = "VALE3"
