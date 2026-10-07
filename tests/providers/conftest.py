from datetime import datetime, timezone

import pytest

from nexo.infrastructure.market_data.policy import ProviderPolicy, ProviderUsage


@pytest.fixture
def policy(tmp_path):
    return ProviderPolicy(
        ProviderUsage(
            tmp_path / "usage.json",
            {
                "brapi": 100,
                "bolsai": 40,
                "Yahoo Finance": 50,
                "CVM": 2,
            },
            now=lambda: datetime(2026, 10, 7, tzinfo=timezone.utc),
        )
    )
