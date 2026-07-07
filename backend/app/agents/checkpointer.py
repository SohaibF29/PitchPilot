"""
AsyncPostgresSaver checkpointer initialization for LangGraph persistence.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.core.logging import get_logger

logger = get_logger(__name__)


class PostgresCheckpointerManager:
    """Manages the lifecycle of the AsyncPostgresSaver checkpointer for LangGraph."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._pool: AsyncConnectionPool | None = None
        self._checkpointer: AsyncPostgresSaver | None = None

    async def initialize(self) -> AsyncPostgresSaver:
        """
        Create connection pool, run database migrations/setup, and return checkpointer.
        """
        if self._checkpointer:
            return self._checkpointer

        logger.info("Initializing AsyncPostgresSaver connection pool...")
        # Create an async pool with autocommit=True (required for setup() schema creation)
        self._pool = AsyncConnectionPool(
            conninfo=self._db_url,
            min_size=2,
            max_size=10,
            kwargs={"autocommit": True},
        )
        
        # Instantiate checkpointer with pool
        self._checkpointer = AsyncPostgresSaver(self._pool)
        
        # Setup tables (idempotent setup check)
        await self._checkpointer.setup()
        logger.info("AsyncPostgresSaver initialized and setup successfully.")
        return self._checkpointer

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            logger.info("Closing checkpointer connection pool...")
            await self._pool.close()
            self._pool = None
            self._checkpointer = None
