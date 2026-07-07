"""
FastAPI Routes for managing OpenAI and Tavily API credentials.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.schemas.requests import SaveApiKeyRequest, SessionApiKeyRequest
from app.api.schemas.responses import ApiKeyHintResponse
from app.dependencies import get_api_key_repository, get_api_key_service
from app.api.dependencies.auth import get_current_user
from app.domain.entities.user import User
from app.domain.interfaces.repositories import IApiKeyRepository
from app.application.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/keys", tags=["api_keys"])


@router.post("", response_model=ApiKeyHintResponse, status_code=status.HTTP_201_CREATED)
async def save_persistent_key(
    payload: SaveApiKeyRequest,
    key_service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Encrypt and store an API key in the database."""
    key_record = await key_service.save_persistent_key(
        user_id=current_user.id,
        provider=payload.provider,
        raw_key=payload.api_key,
    )
    return key_record


@router.post("/session", status_code=status.HTTP_200_OK)
async def save_session_key(
    payload: SessionApiKeyRequest,
    key_service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Store a session-only API key cached in Redis (never persistent)."""
    await key_service.save_session_key(
        user_id=current_user.id,
        provider=payload.provider,
        raw_key=payload.api_key,
        ttl=payload.ttl_seconds,
    )
    return {"message": f"Temporary {payload.provider} key registered successfully."}


@router.get("", response_model=list[ApiKeyHintResponse])
async def list_keys(
    key_repo: IApiKeyRepository = Depends(get_api_key_repository),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List hints of all registered credentials (without revealing values)."""
    keys = await key_repo.list_by_user(user_id=current_user.id)
    return list(keys)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    provider: str,
    key_service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a registered API key."""
    await key_service.delete_key(user_id=current_user.id, provider=provider)
    return None
