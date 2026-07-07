"""
FastAPI Routes for generating and exporting boardroom pitch PDF reports.
"""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from typing import Any

from app.dependencies import get_report_repository, get_report_service, get_meeting_repository
from app.domain.exceptions import EntityNotFoundException
from app.domain.interfaces.repositories import IReportRepository, IMeetingRepository
from app.application.services.report_service import ReportService
from app.api.dependencies.auth import get_current_user
from app.domain.entities.user import User

# Note: Pydantic response schema has name 'Report' but we named it responses.ReportModel in schemas.responses
# Wait, in schemas.responses we didn't define a ReportModel, let's verify.
# Ah, in responses.py we defined Report Response as a dummy? No, let's look at schemas/responses.py.
# In responses.py we have:
# (nothing related to Report? Oh, let's double check)
# Let's inspect the file responses.py contents or rewrite it to be sure.
# Wait, let's write routes/reports.py and return the file directly using FileResponse, which doesn't need complex Pydantic models.
# For metadata details, we can return a JSON with PDF url.

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{meeting_id}", status_code=status.HTTP_201_CREATED)
async def generate_report(
    meeting_id: UUID,
    report_service: ReportService = Depends(get_report_service),
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Compile courtroom analyses and generate a PDF report on disk."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
        
    report = await report_service.generate_pdf_report(meeting_id)
    return {"message": "Report generated successfully.", "pdf_url": report.pdf_url or ""}


@router.get("/{meeting_id}")
async def get_report_metadata(
    meeting_id: UUID,
    report_repo: IReportRepository = Depends(get_report_repository),
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve metadata of a generated report."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
        
    report = await report_repo.get_by_meeting_id(meeting_id)
    if not report:
        raise EntityNotFoundException("Report", str(meeting_id))
    return report.to_dict()


@router.get("/{meeting_id}/download")
async def download_report_pdf(
    meeting_id: UUID,
    report_repo: IReportRepository = Depends(get_report_repository),
    meeting_repo: IMeetingRepository = Depends(get_meeting_repository),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download the generated PDF file for a meeting."""
    meeting = await meeting_repo.get_by_id(meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise EntityNotFoundException("Meeting", str(meeting_id))
        
    report = await report_repo.get_by_meeting_id(meeting_id)
    if not report or not report.pdf_url:
        raise EntityNotFoundException("PDF Report", str(meeting_id))

    # Parse local path from PDF URL
    filename = os.path.basename(report.pdf_url)
    filepath = os.path.join(os.getcwd(), "public", "reports", filename)

    if not os.path.exists(filepath):
        raise EntityNotFoundException("PDF file on disk", filepath)

    return FileResponse(
        path=filepath,
        filename=f"PitchPilot_Report_{meeting_id}.pdf",
        media_type="application/pdf",
    )
