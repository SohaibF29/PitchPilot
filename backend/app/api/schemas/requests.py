"""
Pydantic Request schemas for the presentation layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateMeetingRequest(BaseModel):
    """Payload to create a new pitch boardroom session."""

    title: str = Field(..., min_length=3, max_length=150, description="Title of the startup pitch")
    pitch_text: str = Field(..., min_length=20, max_length=50000, description="Full description of startup concept")


class SaveApiKeyRequest(BaseModel):
    """Payload to persist third-party keys."""

    provider: str = Field(..., description="Provider name e.g. 'openai', 'tavily'")
    api_key: str = Field(..., min_length=10, description="Plaintext API credential to encrypt")


class SessionApiKeyRequest(BaseModel):
    """Payload to register session-only keys."""

    provider: str = Field(..., description="Provider name e.g. 'openai', 'tavily'")
    api_key: str = Field(..., min_length=10, description="Plaintext API credential cached for session duration")
    ttl_seconds: int = Field(default=3600, ge=300, le=86400, description="Key cache TTL")
