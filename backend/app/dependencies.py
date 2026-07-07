"""
FastAPI Dependency Injection container.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.repositories.api_key_repository import ApiKeyRepository
from app.infrastructure.repositories.embedding_repository import EmbeddingRepository
from app.infrastructure.repositories.meeting_repository import MeetingRepository
from app.infrastructure.repositories.report_repository import ReportRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.services.api_key_service import ApiKeyService
from app.application.services.meeting_service import MeetingService
from app.application.services.report_service import ReportService
from app.application.services.search_service import SearchService

settings = get_settings()


async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Provide UserRepository instance."""
    return UserRepository(session)


async def get_meeting_repository(session: AsyncSession = Depends(get_db_session)) -> MeetingRepository:
    """Provide MeetingRepository instance."""
    return MeetingRepository(session)


async def get_report_repository(session: AsyncSession = Depends(get_db_session)) -> ReportRepository:
    """Provide ReportRepository instance."""
    return ReportRepository(session)


async def get_api_key_repository(session: AsyncSession = Depends(get_db_session)) -> ApiKeyRepository:
    """Provide ApiKeyRepository instance."""
    return ApiKeyRepository(session)


async def get_embedding_repository(session: AsyncSession = Depends(get_db_session)) -> EmbeddingRepository:
    """Provide EmbeddingRepository instance."""
    return EmbeddingRepository(session)


async def get_api_key_service(
    key_repo: ApiKeyRepository = Depends(get_api_key_repository),
) -> ApiKeyService:
    """Provide ApiKeyService instance."""
    return ApiKeyService(key_repo)


async def get_search_service(
    embedding_repo: EmbeddingRepository = Depends(get_embedding_repository),
) -> SearchService:
    """Provide SearchService instance."""
    return SearchService(embedding_repo)


async def get_report_service(
    meeting_repo: MeetingRepository = Depends(get_meeting_repository),
    report_repo: ReportRepository = Depends(get_report_repository),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> ReportService:
    """Provide ReportService instance."""
    return ReportService(meeting_repo, report_repo, api_key_service)


# We set checkpointer to None by default for unit testing and local fallback
# In main.py lifespan, checkpointer will be initialized and stored in app.state.checkpointer
# We define a dependency to resolve it
from fastapi import Request

async def get_meeting_service(
    request: Request,
    meeting_repo: MeetingRepository = Depends(get_meeting_repository),
    search_service: SearchService = Depends(get_search_service),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> MeetingService:
    """Provide MeetingService instance, resolving checkpointer from app state lifespan."""
    checkpointer = getattr(request.app.state, "checkpointer", None)
    return MeetingService(
        meeting_repo=meeting_repo,
        checkpointer=checkpointer,
        search_service=search_service,
        api_key_service=api_key_service,
    )
