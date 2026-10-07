import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PUBLIC_SYMBOLS = ("PETR4", "MGLU3", "VALE3", "ITUB4")


@dataclass(frozen=True, slots=True)
class MarketSettings:
    token: str | None = field(default=None, repr=False)
    timeout_seconds: float = 10.0
    batch_size: int = 1
    bolsai_api_key: str | None = field(default=None, repr=False)
    provider_test_mode: bool = True
    brapi_budget: int = 100
    bolsai_budget: int = 40
    yahoo_budget: int = 50
    cvm_budget: int = 2
    brapi_dividends_enabled: bool = False
    bolsai_actions_enabled: bool = False

    @classmethod
    def from_environment(cls, env_path: Path | None = None) -> "MarketSettings":
        # Existing environment takes precedence. Never log credentials or file contents.
        load_dotenv(
            env_path
            if env_path is not None
            else Path(__file__).resolve().parents[4] / ".env",
            override=False,
            encoding="utf-8-sig",
        )
        primary = (os.getenv("BRAPI_TOKEN") or "").strip()
        alias = (os.getenv("BRAPI_API_KEY") or "").strip()
        token = primary or alias
        try:
            size = int(os.getenv("BRAPI_BATCH_SIZE", "1"))
        except ValueError:
            size = 1

        def budget(name: str, default: int) -> int:
            try:
                return max(0, int(os.getenv(name, str(default))))
            except ValueError:
                return default

        return cls(
            token=token or None,
            batch_size=max(1, min(100, size)),
            bolsai_api_key=(os.getenv("BOLSAI_API_KEY") or "").strip() or None,
            provider_test_mode=os.getenv("NEXO_PROVIDER_TEST_MODE", "true").lower()
            == "true",
            brapi_budget=budget("NEXO_BRAPI_SOFT_DAILY_BUDGET", 100),
            bolsai_budget=budget("NEXO_BOLSAI_SOFT_DAILY_BUDGET", 40),
            yahoo_budget=budget("NEXO_YAHOO_SOFT_DAILY_BUDGET", 50),
            cvm_budget=budget("NEXO_CVM_SOFT_DAILY_BUDGET", 2),
            brapi_dividends_enabled=os.getenv(
                "NEXO_BRAPI_DIVIDENDS_ENABLED", "false"
            ).lower()
            == "true",
            bolsai_actions_enabled=os.getenv(
                "NEXO_BOLSAI_ACTIONS_ENABLED", "false"
            ).lower()
            == "true",
        )
