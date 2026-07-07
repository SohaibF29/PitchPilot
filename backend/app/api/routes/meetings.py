"""
FastAPI Routes for managing boardroom meeting sessions and pitches.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.requests import CreateMeetingRequest
from app.api.schemas.responses import MeetingResponse, SemanticSearchMatchResponse
from app.dependencies import get_meeting_repository, get_meeting_service, get_search_service
from app.domain.exceptions import EntityNotFoundException
from app.domain.interfaces.repositories import IMeetingRepository
from app.application.services.meeting_service import MeetingService
from app.application.services.search_service import SearchService
from app.api.dependencies.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/meetings", tags=["meetings"])

# Standard static developer/anonymous user ID for no-auth mode (fallback)
ANONYMOUS_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: CreateMeetingRequest,
    meeting_service: MeetingService = Depends(get_meeting_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new boardroom session with an initial pitch."""
    meeting = await meeting_service.create_meeting(
        user_id=current_user.id,
        title=payload.title,
        pitch_text=payload.pitch_text,
    )
    return meeting


@router.post("/clarify")
async def clarify_pitch(
    payload: CreateMeetingRequest,
    meeting_service: MeetingService = Depends(get_meeting_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Check if a pitch is ambiguous and needs clarification before starting."""
    result = await meeting_service.clarify_pitch(
        user_id=current_user.id,
        title=payload.title,
        pitch_text=payload.pitch_text,
    )
    return result


@router.get("", response_model=list[MeetingResponse])
async def list_meetings(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List past meeting sessions."""
    meetings = await meeting_repo.list_by_user(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return list(meetings)


@router.get("/search", response_model=list[SemanticSearchMatchResponse])
async def semantic_search_meetings(
    q: str = Query(..., min_length=2, description="Semantic query text"),
    limit: int = Query(default=5, ge=1, le=20),
    search_service: SearchService = Depends(get_search_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Perform a vector-based semantic search over past boardroom pitches."""
    results = await search_service.search_meetings(
        user_id=current_user.id,
        query=q,
        limit=limit,
    )
    return results


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting_details(
    meeting_id: UUID,
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed boardroom outputs and metrics for a meeting."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
    return meeting


@router.post("/{meeting_id}/execute", response_model=MeetingResponse)
async def execute_boardroom(
    meeting_id: UUID,
    meeting_service: MeetingService = Depends(get_meeting_service),
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger the multi-agent LangGraph analysis boardroom pipeline."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
        
    meeting = await meeting_service.execute_boardroom(meeting_id)
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a boardroom meeting record."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
        
    deleted = await meeting_repo.delete(meeting_id)
    if not deleted:
        raise EntityNotFoundException("Meeting", str(meeting_id))
    return None
