"""
Domain Repository and Service Interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from app.domain.entities.api_key import UserApiKey
from app.domain.entities.meeting import Meeting
from app.domain.entities.report import Report
from app.domain.entities.user import User


class IUserRepository(ABC):
    """Interface for User data operations."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by email."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Create or update a user."""
        pass


class IMeetingRepository(ABC):
    """Interface for Meeting data operations."""

    @abstractmethod
    async def get_by_id(self, meeting_id: UUID) -> Meeting | None:
        """Retrieve meeting by ID."""
        pass

    @abstractmethod
    async def get_by_thread_id(self, thread_id: str) -> Meeting | None:
        """Retrieve meeting by LangGraph thread ID."""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 20, offset: int = 0) -> Sequence[Meeting]:
        """List meetings for a user with pagination."""
        pass

    @abstractmethod
    async def save(self, meeting: Meeting) -> Meeting:
        """Create or update a meeting."""
        pass

    @abstractmethod
    async def delete(self, meeting_id: UUID) -> bool:
        """Delete a meeting."""
        pass


class IReportRepository(ABC):
    """Interface for Report data operations."""

    @abstractmethod
    async def get_by_id(self, report_id: UUID) -> Report | None:
        """Retrieve report by ID."""
        pass

    @abstractmethod
    async def get_by_meeting_id(self, meeting_id: UUID) -> Report | None:
        """Retrieve report by meeting ID."""
        pass

    @abstractmethod
    async def save(self, report: Report) -> Report:
        """Create or update a report."""
        pass


class IApiKeyRepository(ABC):
    """Interface for API key data operations."""

    @abstractmethod
    async def get_by_id(self, key_id: UUID) -> UserApiKey | None:
        """Retrieve API key by ID."""
        pass

    @abstractmethod
    async def get_by_provider(self, user_id: UUID, provider: str) -> UserApiKey | None:
        """Retrieve API key by provider for a user."""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> Sequence[UserApiKey]:
        """List all API keys for a user."""
        pass

    @abstractmethod
    async def save(self, api_key: UserApiKey) -> UserApiKey:
        """Create or update an API key."""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID, provider: str) -> bool:
        """Delete an API key."""
        pass


class IEmbeddingRepository(ABC):
    """Interface for vector embedding operations."""

    @abstractmethod
    async def save_embedding(
        self, meeting_id: UUID, content: str, embedding: list[float], metadata: dict | None = None
    ) -> None:
        """Save a vector embedding chunk for a meeting."""
        pass

    @abstractmethod
    async def search_similar_meetings(
        self, user_id: UUID, query_embedding: list[float], limit: int = 5, threshold: float = 0.7
    ) -> list[dict]:
        """Query semantic search over past meetings for a specific user."""
        pass
