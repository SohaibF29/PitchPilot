"""
Upstash Redis client implementation for short-term caching, session storage, and rate limiting.
"""

from __future__ import annotations

import json
from typing import Any

from upstash_redis import Redis

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class UpstashRedisCache:
    """Caching service wrapping the Upstash HTTP Redis client."""

    def __init__(self) -> None:
        self._enabled = bool(settings.upstash_redis_rest_url)
        if self._enabled:
            try:
                self._client = Redis(
                    url=settings.upstash_redis_rest_url,
                    token=settings.upstash_redis_rest_token.get_secret_value(),
                )
                logger.info("Upstash Redis connection initialized successfully.")
            except Exception as e:
                logger.error("Failed to initialize Upstash Redis connection: %s", e)
                self._enabled = False
        else:
            logger.warning("Upstash Redis config is missing. Redis operations will be mocked (in-memory).")
            self._mock_db: dict[str, tuple[str, int | None]] = {}

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Deserialized Python object or None.
        """
        if not self._enabled:
            # Fallback to local memory mock
            val_tuple = self._mock_db.get(key)
            if not val_tuple:
                return None
            val, expiry = val_tuple
            # Check expiry (simple timestamp mock or just leave it)
            try:
                return json.loads(val)
            except Exception:
                return val

        try:
            val = self._client.get(key)
            if val is None:
                return None
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return val
        except Exception as e:
            logger.error("Error reading key '%s' from Redis: %s", key, e)
            return None

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """
        Set value in cache with optional TTL (seconds).

        Args:
            key: Cache key.
            value: Python object to cache.
            ex: TTL in seconds.

        Returns:
            True if set successfully.
        """
        serialized = json.dumps(value) if not isinstance(value, (str, bytes)) else value
        if not self._enabled:
            self._mock_db[key] = (serialized, ex)
            return True

        try:
            if ex:
                self._client.setex(key, ex, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error("Error writing key '%s' to Redis: %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key.

        Returns:
            True if key was deleted.
        """
        if not self._enabled:
            return bool(self._mock_db.pop(key, None))

        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error("Error deleting key '%s' from Redis: %s", key, e)
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._enabled:
            return key in self._mock_db
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error("Error checking existence of key '%s' in Redis: %s", key, e)
            return False


# Singleton instance
redis_cache = UpstashRedisCache()
