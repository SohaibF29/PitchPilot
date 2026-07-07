"""
One-shot database migration script.
Creates all required tables in Supabase PostgreSQL.
Run with: python -m scripts.create_tables
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.infrastructure.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables() -> None:
    settings = get_settings()
    db_url = settings.database_url_asyncpg

    logger.info("Connecting to database at %s...", db_url.split("@")[-1])
    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        # Enable pgvector extension (required for meeting_embeddings)
        logger.info("Enabling pgvector extension...")
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("pgvector extension enabled.")
        except Exception as e:
            logger.warning("Could not enable pgvector (may already exist or require superuser): %s", e)

        # Create all tables defined in models.py
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created successfully!")

    await engine.dispose()
    logger.info("Done. Database schema is ready.")


if __name__ == "__main__":
    asyncio.run(create_tables())
