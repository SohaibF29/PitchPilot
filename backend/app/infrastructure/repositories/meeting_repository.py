"""
Meeting repository implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MeetingStatus
from app.domain.entities.meeting import AgentOutput, Meeting, MeetingMetrics, TranscriptEntry
from app.domain.interfaces.repositories import IMeetingRepository
from app.infrastructure.database.models import MeetingModel


class MeetingRepository(IMeetingRepository):
    """SQLAlchemy implementation of IMeetingRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, meeting_id: UUID) -> Meeting | None:
        """Retrieve meeting by ID."""
        result = await self._session.execute(
            select(MeetingModel).where(MeetingModel.id == meeting_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_thread_id(self, thread_id: str) -> Meeting | None:
        """Retrieve meeting by thread ID."""
        result = await self._session.execute(
            select(MeetingModel).where(MeetingModel.thread_id == thread_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_by_user(self, user_id: UUID, limit: int = 20, offset: int = 0) -> Sequence[Meeting]:
        """List meetings for a user with pagination."""
        result = await self._session.execute(
            select(MeetingModel)
            .where(MeetingModel.user_id == user_id)
            .order_by(MeetingModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, meeting: Meeting) -> Meeting:
        """Create or update a meeting."""
        model = await self._session.get(MeetingModel, meeting.id)
        if not model:
            model = MeetingModel(
                id=meeting.id,
                user_id=meeting.user_id,
                title=meeting.title,
                pitch_text=meeting.pitch_text,
                status=meeting.status,
                thread_id=meeting.thread_id,
                agent_outputs=meeting.agent_outputs_dict(),
                transcript=meeting.transcript_list(),
                metrics=meeting.metrics.to_dict(),
                created_at=meeting.created_at,
            )
            self._session.add(model)
        else:
            model.title = meeting.title
            model.pitch_text = meeting.pitch_text
            model.status = meeting.status
            model.agent_outputs = meeting.agent_outputs_dict()
            model.transcript = meeting.transcript_list()
            model.metrics = meeting.metrics.to_dict()
            model.completed_at = meeting.completed_at

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, meeting_id: UUID) -> bool:
        """Delete a meeting."""
        result = await self._session.execute(
            delete(MeetingModel).where(MeetingModel.id == meeting_id)
        )
        return bool(result.rowcount)

    def _to_entity(self, model: MeetingModel) -> Meeting:
        """Map ORM to domain entity."""
        # Deserialize agent outputs
        agent_outputs = {}
        if model.agent_outputs:
            for name, out in model.agent_outputs.items():
                agent_outputs[name] = AgentOutput(
                    agent_name=out.get("agent_name", name),
                    content=out.get("content", ""),
                    tokens_used=out.get("tokens_used", 0),
                    prompt_tokens=out.get("prompt_tokens", 0),
                    completion_tokens=out.get("completion_tokens", 0),
                    latency_ms=out.get("latency_ms", 0.0),
                    model=out.get("model", "gpt-4o"),
                    retry_count=out.get("retry_count", 0),
                    timestamp=datetime.fromisoformat(out["timestamp"]) if out.get("timestamp") else datetime.utcnow(),
                )

        # Deserialize transcript entries
        transcript = []
        if model.transcript:
            for entry in model.transcript:
                transcript.append(
                    TranscriptEntry(
                        role=entry.get("role", "unknown"),
                        content=entry.get("content", ""),
                        timestamp=datetime.fromisoformat(entry["timestamp"]) if entry.get("timestamp") else datetime.utcnow(),
                        is_voice=entry.get("is_voice", False),
                    )
                )

        # Deserialize metrics
        metrics = MeetingMetrics()
        if model.metrics:
            metrics = MeetingMetrics(
                total_tokens=model.metrics.get("total_tokens", 0),
                prompt_tokens=model.metrics.get("prompt_tokens", 0),
                completion_tokens=model.metrics.get("completion_tokens", 0),
                total_latency_ms=model.metrics.get("total_latency_ms", 0.0),
                estimated_cost=model.metrics.get("estimated_cost", 0.0),
                total_retries=model.metrics.get("total_retries", 0),
                model=model.metrics.get("model", "gpt-4o"),
                agents_completed=model.metrics.get("agents_completed", 0),
                agents_total=model.metrics.get("agents_total", 5),
            )

        return Meeting(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            pitch_text=model.pitch_text,
            status=MeetingStatus(model.status),
            thread_id=model.thread_id,
            agent_outputs=agent_outputs,
            transcript=transcript,
            metrics=metrics,
            created_at=model.created_at,
            completed_at=model.completed_at,
            updated_at=model.updated_at,
        )
