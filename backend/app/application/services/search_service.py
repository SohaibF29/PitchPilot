"""
Semantic search service for PitchPilot meetings using OpenAI embeddings and pgvector.
"""

from __future__ import annotations

from uuid import UUID

from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.core.logging import get_logger
from app.domain.interfaces.repositories import IEmbeddingRepository

logger = get_logger(__name__)
settings = get_settings()


class SearchService:
    """Orchestrates generating embeddings and executing semantic queries over past pitches."""

    def __init__(self, embedding_repo: IEmbeddingRepository) -> None:
        self._embedding_repo = embedding_repo

    def _get_embeddings_client(self, api_key: str | None = None) -> OpenAIEmbeddings:
        """Resolve OpenAI embeddings client with optional user-supplied key."""
        key = api_key or settings.openai_api_key.get_secret_value()
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=key,
        )

    async def index_meeting(self, meeting_id: UUID, title: str, pitch_text: str, api_key: str | None = None) -> None:
        """
        Generate embedding for a startup pitch and save it to vector storage.

        Args:
            meeting_id: Meeting unique identifier.
            title: Title of startup idea.
            pitch_text: Main pitch text to embed.
            api_key: Optional client-supplied API key.
        """
        if not pitch_text:
            return

        try:
            embeddings_client = self._get_embeddings_client(api_key)
            # Embed both title and body for better retrieval
            content_to_embed = f"Title: {title}\n\nPitch: {pitch_text}"
            
            # Generate vector embedding asynchronously
            embedding = await embeddings_client.aembed_query(content_to_embed)

            await self._embedding_repo.save_embedding(
                meeting_id=meeting_id,
                content=content_to_embed,
                embedding=embedding,
                metadata={"title": title},
            )
            logger.info("Successfully indexed meeting '%s' for semantic search.", meeting_id)
        except Exception as e:
            logger.error("Failed to generate embedding / index meeting %s: %s", meeting_id, e)

    async def search_meetings(
        self, user_id: UUID, query: str, api_key: str | None = None, limit: int = 5, threshold: float = 0.7
    ) -> list[dict]:
        """
        Perform semantic vector search over a user's past pitches.

        Args:
            user_id: Owner of meetings.
            query: Semantic search query.
            api_key: Optional client-supplied API key.
            limit: Maximum matches.
            threshold: Cosine similarity lower bound.

        Returns:
            List of matching items containing meeting_id, title, similarity.
        """
        if not query:
            return []

        try:
            embeddings_client = self._get_embeddings_client(api_key)
            query_embedding = await embeddings_client.aembed_query(query)
            
            return await self._embedding_repo.search_similar_meetings(
                user_id=user_id,
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold,
            )
        except Exception as e:
            logger.error("Semantic search failed for user %s: %s", user_id, e)
            return []
