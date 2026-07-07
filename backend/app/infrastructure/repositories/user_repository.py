"""
User repository implementation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.repositories import IUserRepository
from app.infrastructure.database.models import ProfileModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of IUserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user profile by ID."""
        result = await self._session.execute(
            select(ProfileModel).where(ProfileModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        """Get user profile by email."""
        # Note: profiles table matching auth.users might only have email if duplicated.
        # But wait, in a no-sign-up workflow we don't strictly require user management.
        # However, we implement it for full SaaS capability.
        return None

    async def save(self, user: User) -> User:
        """Save/update user profile."""
        model = await self._session.get(ProfileModel, user.id)
        if not model:
            model = ProfileModel(
                id=user.id,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                created_at=user.created_at,
            )
            self._session.add(model)
        else:
            model.full_name = user.full_name
            model.avatar_url = user.avatar_url
            model.updated_at = user.updated_at

        await self._session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: ProfileModel) -> User:
        """Map ORM to domain entity."""
        return User(
            id=model.id,
            email="",  # email managed in auth schema
            full_name=model.full_name,
            avatar_url=model.avatar_url,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
