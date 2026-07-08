"""
API Key management service.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.api_key import UserApiKey
from app.domain.exceptions import InvalidRequestException
from app.domain.interfaces.repositories import IApiKeyRepository
from app.infrastructure.cache.redis_cache import redis_cache
from app.infrastructure.encryption.fernet_encryption import encryptor


class ApiKeyService:
    """Orchestrates API key CRUD operations, encryption, and temporary session keys."""

    def __init__(self, key_repo: IApiKeyRepository) -> None:
        self._key_repo = key_repo

    async def get_decrypted_key(self, user_id: UUID, provider: str) -> str | None:
        """
        Retrieve and decrypt a user's API key.

        First checks temporary session-only keys in cache, then persistent DB storage.
        """
        # 1. Check temporary session cache
        cache_key = f"session_key:{user_id}:{provider}"
        cached_val = redis_cache.get(cache_key)
        if cached_val:
            return cached_val

        # 2. Check persistent database
        db_key = await self._key_repo.get_by_provider(user_id, provider)
        if db_key:
            return encryptor.decrypt(db_key.encrypted_key)

        return None

    async def get_all_decrypted_keys(self, user_id: UUID) -> dict[str, str]:
        """Fetch and decrypt all persistent and session API keys for a user in a single DB query."""
        keys = {}
        
        # 1. Fetch persistent keys (1 round-trip)
        db_keys = await self._key_repo.list_by_user(user_id)
        for db_key in db_keys:
            keys[db_key.provider] = encryptor.decrypt(db_key.encrypted_key)
            
        # 2. Check temporary session cache for overrides
        for provider in ["openai", "tavily"]:
            cache_key = f"session_key:{user_id}:{provider}"
            cached_val = redis_cache.get(cache_key)
            if cached_val:
                keys[provider] = cached_val
                
        return keys

    async def save_persistent_key(self, user_id: UUID, provider: str, raw_key: str) -> UserApiKey:
        """Encrypt and persist an API key in the database."""
        if not raw_key:
            raise InvalidRequestException("API key cannot be empty.")

        encrypted = encryptor.encrypt(raw_key)
        key_hint = f"{raw_key[:3]}...{raw_key[-4:]}" if len(raw_key) > 8 else "****"

        # Check if already exists to overwrite or create new
        existing = await self._key_repo.get_by_provider(user_id, provider)
        if existing:
            existing.encrypted_key = encrypted
            existing.key_hint = key_hint
            api_key = await self._key_repo.save(existing)
        else:
            api_key = UserApiKey(
                user_id=user_id,
                provider=provider,
                encrypted_key=encrypted,
                key_hint=key_hint,
            )
            api_key = await self._key_repo.save(api_key)

        return api_key

    async def save_session_key(self, user_id: UUID, provider: str, raw_key: str, ttl: int = 3600) -> None:
        """Save a temporary session-only key in Redis (never persisted to DB)."""
        if not raw_key:
            raise InvalidRequestException("API key cannot be empty.")
        cache_key = f"session_key:{user_id}:{provider}"
        redis_cache.set(cache_key, raw_key, ex=ttl)

    async def delete_key(self, user_id: UUID, provider: str) -> bool:
        """Delete key from database and cache."""
        cache_key = f"session_key:{user_id}:{provider}"
        redis_cache.delete(cache_key)
        return await self._key_repo.delete(user_id, provider)
