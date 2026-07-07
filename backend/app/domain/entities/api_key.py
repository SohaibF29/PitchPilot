"""
API key entity — representing stored third-party credentials.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class UserApiKey:
    """Represents a third-party API key stored securely."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    provider: str = ""  # "openai", "tavily" etc.
    encrypted_key: bytes = b""
    key_hint: str = ""  # Last 4 characters (e.g. "sk-...a1b2")
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary representation (excluding encrypted key)."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "provider": self.provider,
            "key_hint": self.key_hint,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
