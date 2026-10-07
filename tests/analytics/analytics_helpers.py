from datetime import datetime
from decimal import Decimal

from nexo.domain.models.asset import Asset


def analytics_trade(
    identity, symbol="PETR4", quantity="10", price="30", kind=None, hour=10
):
    from nexo.domain.enums.transaction_type import TransactionType
    from nexo.domain.models.transaction import Transaction

    return Transaction(
        identity,
        Asset(symbol),
        kind or TransactionType.BUY,
        Decimal(quantity),
        Decimal(price),
        Decimal(0),
        datetime(2026, 1, 1, hour),  # noqa: DTZ001 - Ledger wall time is preserved.
    )
