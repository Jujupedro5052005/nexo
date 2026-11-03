"""Typed AI boundary. Extracted knowledge never defines executable Python."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class SourceReference(Record):
    title: str
    uri: str
    timestamp: str | None = None
    excerpt: str = ""


class Methodology(Record):
    methodology_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,60}$")
    name: str
    version: int = Field(ge=1)
    description: str
    applicable_asset_types: tuple[str, ...]
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    formula_reference: str
    assumptions: tuple[str, ...]
    constraints: tuple[str, ...]
    output_fields: tuple[str, ...] = ("theoretical_value", "ceiling_price")
    source_references: tuple[SourceReference, ...] = ()
    review_status: Literal[
        "draft", "pending_review", "approved", "rejected", "superseded"
    ] = "draft"
    origin: Literal["source", "inference", "nexo", "synthetic"] = "inference"
    confidence: Decimal = Field(default=Decimal(0), ge=0, le=1)
    created_at: datetime = Field(default_factory=utc_now)
    reviewed_by: str | None = None


class ToolCall(Record):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(Record):
    name: str
    available: bool
    data: Any = None
    error: str | None = None
    queried_at: datetime = Field(default_factory=utc_now)


class KnowledgeHit(Record):
    document_id: str
    version: str
    text: str
    sources: tuple[SourceReference, ...] = ()


class ChatMessage(Record):
    role: Literal["user", "assistant"]
    text: str
    created_at: datetime = Field(default_factory=utc_now)


class AnalysisRequest(Record):
    question: str = Field(min_length=1, max_length=6000)
    conversation_id: str = Field(default="default", pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    portfolio_id: int | None = Field(default=None, gt=0, strict=True)
    symbol: str = Field(default="", max_length=24, pattern=r"^[a-zA-Z0-9.^=_-]*$")
    methodology_id: str = ""
    asset_type: Literal["stock", "bank", "insurer", "fii", "etf", "bond", "crypto"] = (
        "stock"
    )
    assumptions: dict[str, Any] = Field(default_factory=dict)
    allow_cloud: bool = False
    analysis_mode: Literal["chat", "deep"] = "chat"
    focus_symbols: tuple[
        Annotated[str, Field(max_length=24, pattern=r"^[A-Z0-9.^=_-]+$")], ...
    ] = Field(default=(), max_length=20)
    allow_estimates: bool = True


class AnalysisResponse(Record):
    markdown: str
    evidence: tuple[ToolResult, ...] = ()
    knowledge: tuple[KnowledgeHit, ...] = ()
    mode: str
    created_at: datetime = Field(default_factory=utc_now)
    report: dict[str, Any] = Field(default_factory=dict)


class EstimatedScenario(Record):
    label: Literal["conservador", "base", "otimista"]
    required_return: Decimal = Field(
        ge=Decimal("0.06"), le=Decimal("0.40"), decimal_places=4
    )
    growth: Decimal = Field(ge=Decimal("-0.05"), le=Decimal("0.06"), decimal_places=4)
    target_yield: Decimal = Field(
        ge=Decimal("0.03"), le=Decimal("0.20"), decimal_places=4
    )
    justification: str = Field(min_length=20, max_length=1500)


class ScenarioProposal(Record):
    scenarios: tuple[EstimatedScenario, ...] = Field(min_length=3, max_length=3)


class IntelligenceError(RuntimeError):
    """Only safe messages cross the UI boundary."""


class QuotaExceeded(IntelligenceError):
    pass
