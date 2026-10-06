import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class MarketSettings:
    token: str | None = field(default=None, repr=False)
    timeout_seconds: float = 10.0
    batch_size: int = 5

    @classmethod
    def from_environment(cls) -> "MarketSettings":
        # Existing environment takes precedence. Never log credentials or file contents.
        load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
        token = (os.getenv("BRAPI_TOKEN") or os.getenv("BRAPI_API_KEY") or "").strip()
        try:
            size = int(os.getenv("BRAPI_BATCH_SIZE", "5"))
        except ValueError:
            size = 5
        return cls(token=token or None, batch_size=max(1, min(100, size)))
