"""
Meeting entity — represents an AI boardroom session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import MeetingStatus


@dataclass
class TranscriptEntry:
    """A single entry in the meeting transcript."""

    role: str  # "user", "moderator", "market_analyst", etc.
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_voice: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_voice": self.is_voice,
        }


@dataclass
class AgentOutput:
    """Structured output from a single agent."""

    agent_name: str
    content: str  # JSON string with structured analysis
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    model: str = "gpt-4o"
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_name": self.agent_name,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "model": self.model,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MeetingMetrics:
    """Aggregated metrics for a meeting session."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_latency_ms: float = 0.0
    estimated_cost: float = 0.0
    total_retries: int = 0
    model: str = "gpt-4o"
    agents_completed: int = 0
    agents_total: int = 5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_latency_ms": self.total_latency_ms,
            "estimated_cost": round(self.estimated_cost, 6),
            "total_retries": self.total_retries,
            "model": self.model,
            "agents_completed": self.agents_completed,
            "agents_total": self.agents_total,
        }


@dataclass
class Meeting:
    """Represents an AI boardroom meeting session."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    title: str = ""
    pitch_text: str = ""
    status: MeetingStatus = MeetingStatus.CREATED
    thread_id: str = ""
    agent_outputs: dict[str, AgentOutput] = field(default_factory=dict)
    transcript: list[TranscriptEntry] = field(default_factory=list)
    metrics: MeetingMetrics = field(default_factory=MeetingMetrics)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if the meeting is still in progress."""
        return self.status in (MeetingStatus.CREATED, MeetingStatus.IN_PROGRESS)

    def is_complete(self) -> bool:
        """Check if the meeting has completed successfully."""
        return self.status == MeetingStatus.COMPLETED

    def can_resume(self) -> bool:
        """Check if the meeting can be resumed."""
        return self.status == MeetingStatus.INTERRUPTED

    def agent_outputs_dict(self) -> dict[str, Any]:
        """Convert agent outputs to serializable dict."""
        return {
            name: output.to_dict()
            for name, output in self.agent_outputs.items()
        }

    def transcript_list(self) -> list[dict[str, Any]]:
        """Convert transcript to serializable list."""
        return [entry.to_dict() for entry in self.transcript]
