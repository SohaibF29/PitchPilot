"""
Report entity — represents the generated PDF report and sections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Report:
    """Represents a generated startup pitch report."""

    id: UUID = field(default_factory=uuid4)
    meeting_id: UUID = field(default_factory=uuid4)
    sections: dict[str, str] = field(default_factory=dict)  # Keys from constants.REPORT_SECTIONS
    pdf_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_complete(self) -> bool:
        """Check if all required sections are present."""
        from app.core.constants import REPORT_SECTIONS
        return all(section in self.sections for section in REPORT_SECTIONS)

    def get_section(self, section_name: str) -> str:
        """Get the content of a specific report section."""
        return self.sections.get(section_name, "")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "meeting_id": str(self.meeting_id),
            "sections": self.sections,
            "pdf_url": self.pdf_url,
            "created_at": self.created_at.isoformat(),
        }
