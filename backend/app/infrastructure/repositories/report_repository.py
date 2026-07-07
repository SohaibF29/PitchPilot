"""
Report repository implementation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import Report
from app.domain.interfaces.repositories import IReportRepository
from app.infrastructure.database.models import ReportModel


class ReportRepository(IReportRepository):
    """SQLAlchemy implementation of IReportRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, report_id: UUID) -> Report | None:
        """Retrieve report by ID."""
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_meeting_id(self, meeting_id: UUID) -> Report | None:
        """Retrieve report by meeting ID."""
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.meeting_id == meeting_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def save(self, report: Report) -> Report:
        """Create or update a report."""
        model = await self._session.get(ReportModel, report.id)
        if not model:
            model = ReportModel(
                id=report.id,
                meeting_id=report.meeting_id,
                sections=report.sections,
                pdf_url=report.pdf_url,
                created_at=report.created_at,
            )
            self._session.add(model)
        else:
            model.sections = report.sections
            model.pdf_url = report.pdf_url

        await self._session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: ReportModel) -> Report:
        """Map ORM to domain entity."""
        return Report(
            id=model.id,
            meeting_id=model.meeting_id,
            sections=model.sections,
            pdf_url=model.pdf_url,
            created_at=model.created_at,
        )
