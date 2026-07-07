"""
PitchPilot FastAPI Application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.api.router import api_router
from app.config import get_settings
from app.core.logging import setup_logging
from app.agents.checkpointer import PostgresCheckpointerManager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown lifecycles."""
    # 1. Setup structured logging
    setup_logging(log_level=settings.log_level, json_format=settings.is_production)
    
    # 2. Setup LangGraph Postgres Checkpointer
    checkpointer_manager = PostgresCheckpointerManager(settings.database_url_psycopg)
    try:
        # Build connections and execute checkpointer DDLs
        checkpointer = await checkpointer_manager.initialize()
        app.state.checkpointer = checkpointer
    except Exception as e:
        # Fallback to in-memory/none checkpointing on local dev if DB connection fails
        # This keeps the backend server alive for testing even without a running database!
        import logging
        logging.getLogger(__name__).warning(
            "Failed to connect database checkpointer, compiling graph without persistence: %s", e
        )
        app.state.checkpointer = None

    yield

    # 3. Shutdown connections
    if checkpointer_manager:
        await checkpointer_manager.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler middleware
app.add_middleware(ErrorHandlerMiddleware)

# Expose API routes
app.include_router(api_router)

# Mount public folder for static file downloads (generated PDFs)
import os
os.makedirs(os.path.join(os.getcwd(), "public", "reports"), exist_ok=True)
app.mount("/static", StaticFiles(directory="public"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
