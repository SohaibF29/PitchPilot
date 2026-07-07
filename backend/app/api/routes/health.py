"""
Liveness and readiness endpoints for PitchPilot.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.infrastructure.cache.redis_cache import redis_cache

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Basic endpoint to verify the service is running."""
    return {"status": "healthy"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Verify database and caching connections are active."""
    status_details = {
        "status": "ready",
        "database": "unhealthy",
        "cache": "unhealthy",
    }

    # 1. Test database connection
    try:
        await db.execute(text("SELECT 1"))
        status_details["database"] = "healthy"
    except Exception:
        status_details["status"] = "not_ready"

    # 2. Test cache connection
    try:
        redis_cache.set("health_check_ping", "pong", ex=5)
        if redis_cache.get("health_check_ping") == "pong":
            status_details["cache"] = "healthy"
    except Exception:
        # We don't fail readiness on Redis dev mock fallback
        if not redis_cache._enabled:
            status_details["cache"] = "healthy (mocked)"
        else:
            status_details["status"] = "not_ready"

    return status_details
from typing import Any
