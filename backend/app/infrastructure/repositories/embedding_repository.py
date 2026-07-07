"""
Embedding repository implementation for semantic search using pgvector.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories import IEmbeddingRepository
from app.infrastructure.database.models import MeetingEmbeddingModel, MeetingModel


class EmbeddingRepository(IEmbeddingRepository):
    """SQLAlchemy implementation of IEmbeddingRepository using pgvector."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_embedding(
        self, meeting_id: UUID, content: str, embedding: list[float], metadata: dict | None = None
    ) -> None:
        """Save a vector embedding chunk for a meeting."""
        model = MeetingEmbeddingModel(
            meeting_id=meeting_id,
            content=content,
            embedding=embedding,
            metadata_json=metadata or {},
        )
        self._session.add(model)
        await self._session.flush()

    async def search_similar_meetings(
        self, user_id: UUID, query_embedding: list[float], limit: int = 5, threshold: float = 0.7
    ) -> list[dict]:
        """
        Query semantic search over past meetings for a specific user using pgvector.

        Uses cosine distance similarity (1 - (embedding <=> query_embedding)).
        """
        # We perform join on meetings to filter by user_id and return matching meetings
        query = (
            select(
                MeetingEmbeddingModel.content,
                MeetingEmbeddingModel.meeting_id,
                MeetingModel.title,
                # Cosine similarity formula: 1 - (a <=> b)
                (1 - MeetingEmbeddingModel.embedding.cosine_distance(query_embedding)).label("similarity"),
            )
            .join(MeetingModel, MeetingModel.id == MeetingEmbeddingModel.meeting_id)
            .where(MeetingModel.user_id == user_id)
            .where((1 - MeetingEmbeddingModel.embedding.cosine_distance(query_embedding)) >= threshold)
            .order_by(text("similarity DESC"))
            .limit(limit)
        )

        result = await self._session.execute(query)
        rows = result.all()

        return [
            {
                "content": row.content,
                "meeting_id": str(row.meeting_id),
                "title": row.title,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]
