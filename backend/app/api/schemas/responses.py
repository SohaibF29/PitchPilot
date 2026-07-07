"""
Pydantic Response schemas for the presentation layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentOutputResponse(BaseModel):
    """Response containing individual agent analysis output."""

    agent_name: str
    content: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    model: str
    retry_count: int
    timestamp: datetime


class TranscriptEntryResponse(BaseModel):
    """Single speech transcript message bubble."""

    role: str
    content: str
    timestamp: datetime
    is_voice: bool


class MeetingMetricsResponse(BaseModel):
    """Meeting execution diagnostics and cost metrics."""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_latency_ms: float
    estimated_cost: float
    total_retries: int
    model: str
    agents_completed: int
    agents_total: int


class MeetingResponse(BaseModel):
    """Complete boardroom meeting info."""

    id: UUID
    user_id: UUID | None
    title: str
    pitch_text: str
    status: str
    thread_id: str
    agent_outputs: dict[str, AgentOutputResponse]
    transcript: list[TranscriptEntryResponse]
    metrics: MeetingMetricsResponse
    created_at: datetime
    completed_at: datetime | None
    updated_at: datetime


class ApiKeyHintResponse(BaseModel):
    """Hint indicating a key is stored without exposing the value."""

    id: UUID
    provider: str
    key_hint: str
    created_at: datetime
    updated_at: datetime


class SemanticSearchMatchResponse(BaseModel):
    """Semantic match result."""

    meeting_id: UUID
    title: str
    content: str
    similarity: float
