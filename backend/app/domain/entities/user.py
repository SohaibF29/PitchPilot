"""
User entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class User:
    """Represents a platform user."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    full_name: str = ""
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def display_name(self) -> str:
        """Return display name, falling back to email prefix."""
        if self.full_name:
            return self.full_name
        if self.email:
            return self.email.split("@")[0]
        return "Anonymous"
