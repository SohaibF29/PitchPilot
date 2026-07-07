"""
Main API Router grouping all domain subrouters.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import api_keys, health, meetings, reports
from app.api.websockets import meeting_ws, voice_ws

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(meetings.router)
api_router.include_router(reports.router)
api_router.include_router(api_keys.router)
api_router.include_router(meeting_ws.router)
api_router.include_router(voice_ws.router)

