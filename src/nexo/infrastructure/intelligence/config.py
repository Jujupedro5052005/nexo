import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field

from nexo.core.paths import environment_file
from nexo.domain.models.intelligence import Record

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class AISettings(Record):
    enabled: bool = True
    api_key: str = Field(default="", repr=False, exclude=True)
    provider: Literal["auto", "mock", "gemini"] = "auto"
    model: str = DEFAULT_MODEL
    extraction_model: str = DEFAULT_MODEL
    video_model: str = DEFAULT_MODEL
    retrieval_model: str = DEFAULT_MODEL
    max_input_tokens: int = Field(default=32000, ge=1000, le=100000)
    max_output_tokens: int = Field(default=2048, ge=128, le=8192)
    daily_request_limit: int = Field(default=20, ge=0, le=10000)
    daily_token_limit: int = Field(default=200000, ge=0)
    max_tool_calls: int = Field(default=8, ge=1, le=12)
    file_search_store: str = Field(
        default="", pattern=r"^$|^fileSearchStores/[A-Za-z0-9_-]+$"
    )
    configuration_error: str = ""
    youtube_api_key: str = Field(default="", repr=False, exclude=True)
    project_id: str = "gen-lang-client-0662974523"
    project_number: str = "1029731024680"
    input_usd_per_million: str = ""
    output_usd_per_million: str = ""

    @property
    def cloud(self) -> bool:
        return self.provider == "gemini" or (
            self.provider == "auto" and bool(self.api_key)
        )

    @classmethod
    def from_environment(cls, path: Path | None = None) -> "AISettings":
        load_dotenv(
            path or environment_file(),
            override=False,
            encoding="utf-8-sig",
        )
        fields: dict[str, object] = {}
        for name in cls.model_fields:
            key = {
                "api_key": "GEMINI_API_KEY",
                "youtube_api_key": "YOUTUBE_API_KEY",
            }.get(name, f"NEXO_AI_{name.upper()}")
            value = os.environ.get(key, "").strip()
            if value:
                fields[name] = value
        try:
            return cls.model_validate(fields)
        except ValueError:
            return cls(
                enabled=False,
                provider="mock",
                configuration_error="Configuração da IA inválida. Confira modelos, store e limites no .env.example; o restante do Nexo permanece disponível.",
            )
