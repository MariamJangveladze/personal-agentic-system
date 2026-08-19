"""Typed workflow state shared by CLI and MCP entry points."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    DRAFTED = "drafted"
    APPROVED = "approved"
    REJECTED = "rejected"


class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    objective: str
    status: RunStatus = RunStatus.DRAFTED
    model: str
    sources: list[str] = Field(default_factory=list)
    draft: str
    reviewer: str | None = None
    review_reason: str | None = None
    artifact_path: str | None = None
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

