"""
API key repository implementation.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.api_key import UserApiKey
from app.domain.interfaces.repositories import IApiKeyRepository
from app.infrastructure.database.models import ApiKeyModel


class ApiKeyRepository(IApiKeyRepository):
    """SQLAlchemy implementation of IApiKeyRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, key_id: UUID) -> UserApiKey | None:
        """Retrieve API key by ID."""
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.id == key_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_provider(self, user_id: UUID, provider: str) -> UserApiKey | None:
        """Retrieve API key by provider for a user."""
        result = await self._session.execute(
            select(ApiKeyModel)
            .where(ApiKeyModel.user_id == user_id)
            .where(ApiKeyModel.provider == provider)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_by_user(self, user_id: UUID) -> Sequence[UserApiKey]:
        """List all API keys for a user."""
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.user_id == user_id)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, api_key: UserApiKey) -> UserApiKey:
        """Create or update an API key."""
        model = await self._session.get(ApiKeyModel, api_key.id)
        if not model:
            model = ApiKeyModel(
                id=api_key.id,
                user_id=api_key.user_id,
                provider=api_key.provider,
                encrypted_key=api_key.encrypted_key,
                key_hint=api_key.key_hint,
                created_at=api_key.created_at,
            )
            self._session.add(model)
        else:
            model.encrypted_key = api_key.encrypted_key
            model.key_hint = api_key.key_hint

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, user_id: UUID, provider: str) -> bool:
        """Delete an API key."""
        result = await self._session.execute(
            delete(ApiKeyModel)
            .where(ApiKeyModel.user_id == user_id)
            .where(ApiKeyModel.provider == provider)
        )
        return bool(result.rowcount)

    def _to_entity(self, model: ApiKeyModel) -> UserApiKey:
        """Map ORM to domain entity."""
        return UserApiKey(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,
            encrypted_key=model.encrypted_key,
            key_hint=model.key_hint,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
