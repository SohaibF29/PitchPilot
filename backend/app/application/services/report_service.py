"""
PDF Report generation service using WeasyPrint.
"""

from __future__ import annotations

import os
from datetime import datetime
from uuid import UUID

from jinja2 import Environment, PackageLoader, select_autoescape
from app.config import get_settings
from app.core.constants import REPORT_SECTIONS
from app.core.logging import get_logger
from app.domain.entities.report import Report
from app.domain.exceptions import EntityNotFoundException, InvalidRequestException
from app.domain.interfaces.repositories import IMeetingRepository, IReportRepository

import io
import httpx
from openai import AsyncOpenAI
from xhtml2pdf import pisa
from app.application.services.api_key_service import ApiKeyService



logger = get_logger(__name__)
settings = get_settings()

# Initialize Jinja2 environment for loading PDF HTML templates
jinja_env = Environment(
    loader=PackageLoader("app", "infrastructure/pdf/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


class ReportService:
    """Orchestrates structured report HTML rendering and PDF compiling using xhtml2pdf."""

    def __init__(
        self,
        meeting_repo: IMeetingRepository,
        report_repo: IReportRepository,
        api_key_service: ApiKeyService | None = None,
    ) -> None:
        self._meeting_repo = meeting_repo
        self._report_repo = report_repo
        self._api_key_service = api_key_service



    async def generate_pdf_report(self, meeting_id: UUID) -> Report:
        """
        Extract agent outputs, build report sections, render HTML template, and write PDF.
        """
        meeting = await self._meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise EntityNotFoundException("Meeting", str(meeting_id))

        if not meeting.is_complete():
            raise InvalidRequestException("Cannot generate report for incomplete boardroom meeting.")

        # Check if report already exists
        existing_report = await self._report_repo.get_by_meeting_id(meeting_id)
        if existing_report and existing_report.pdf_url:
            return existing_report



        # 2. Map agent outputs to report sections
        sections = {}
        for section in REPORT_SECTIONS:
            sections[section] = self._resolve_section_content(meeting, section)

        report = Report(
            meeting_id=meeting_id,
            sections=sections,
        )

        # 3. Render HTML template using Jinja2
        try:
            template = jinja_env.get_template("report.html")
        except Exception:
            from jinja2 import DictLoader
            fallback_loader = DictLoader({
                "report.html": "<html><body><h1>Pitch Report: {{ meeting.title }}</h1>{% if chart_path %}<img src=\"{{ chart_path }}\" />{% endif %}{% for k, v in sections.items() %}<h2>{{ k }}</h2><p>{{ v }}</p>{% endfor %}</body></html>"
            })
            fallback_env = Environment(loader=fallback_loader)
            template = fallback_env.get_template("report.html")

        html_content = template.render(
            meeting=meeting,
            sections=sections,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # 4. Compile PDF using xhtml2pdf
        try:
            storage_dir = os.path.join(os.getcwd(), "public", "reports")
            os.makedirs(storage_dir, exist_ok=True)

            filename = f"report_{meeting_id}.pdf"
            filepath = os.path.join(storage_dir, filename)

            # Generate PDF bytes via xhtml2pdf (pisa)
            pdf_buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            if pisa_status.err:
                raise InvalidRequestException("PDF generation failed via xhtml2pdf.")

            with open(filepath, "wb") as f:
                f.write(pdf_buffer.getvalue())

            report.pdf_url = f"/static/reports/{filename}"

            # Save report metadata to DB
            saved_report = await self._report_repo.save(report)
            logger.info("Successfully generated PDF report via xhtml2pdf for meeting %s.", meeting_id)
            return saved_report

        except Exception as e:
            logger.error("xhtml2pdf PDF compilation failed for meeting %s: %s", meeting_id, e)
            raise InvalidRequestException(f"PDF generation failed: {e}")

    def _format_content(self, content: str) -> str:
        """Parse markdown string content and format it to HTML for PDF generation."""
        import markdown
        try:
            return markdown.markdown(content)
        except Exception:
            return content.replace("\n", "<br/>")

    def _resolve_section_content(self, meeting: Any, section: str) -> str:
        """Map generic report sections to specific agent output sections."""
        outputs = meeting.agent_outputs
        
        # Simple extraction rules based on agent specializations
        content = ""
        if section == "executive_summary":
            content = outputs.get("moderator").content if "moderator" in outputs else meeting.pitch_text
        elif section == "market_analysis":
            content = outputs.get("market_analyst").content if "market_analyst" in outputs else "Pending analyst review."
        elif section == "mvp_recommendation":
            content = outputs.get("product_manager").content if "product_manager" in outputs else "Pending PM review."
        elif section == "revenue_model":
            content = outputs.get("finance_advisor").content if "finance_advisor" in outputs else "Pending financial review."
        elif section == "technical_review":
            content = outputs.get("technical_architect").content if "technical_architect" in outputs else "Pending technical architect review."
        elif section == "final_recommendation":
            # Combine moderator final remarks
            content = outputs.get("moderator").content if "moderator" in outputs else "No recommendation available."
        else:
            # Fallback to general outputs
            combined = []
            for name, output in outputs.items():
                if section in output.content.lower():
                    combined.append(output.content)
            content = "\n\n".join(combined) if combined else f"Review in-progress by the boardroom."
            
        return self._format_content(content)
