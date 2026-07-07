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

    async def _generate_stats_visual(self, meeting: Any, openai_key: str) -> str | None:
        """
        Extracts stats from meeting reports and generates an infographic using DALL-E 3.
        Saves the file locally and returns the local absolute filepath.
        """
        try:
            reports_text = ""
            for role, out in meeting.agent_outputs.items():
                reports_text += f"[{role}]: {out.content}\n\n"

            prompt_extraction = (
                "Based on the following boardroom reports, identify the key statistics, percentages, and metrics. "
                "Write a highly descriptive, professional prompt for DALL-E 3 to generate a clean, modern corporate infographic "
                "or business illustration showing these stats. The prompt must request a dark blue/indigo color palette matching "
                "a premium SaaS tool, with clear visual structures and no gibberish text or labels. "
                "Return ONLY the DALL-E 3 prompt string, nothing else."
            )

            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage

            llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=openai_key,
                temperature=0.7,
            )

            res = await llm.ainvoke([
                SystemMessage(content=prompt_extraction),
                ("user", f"Boardroom Reports:\n{reports_text}"),
            ])

            dalle_prompt = res.content.strip()
            logger.info("Generated DALL-E prompt for statistics: %s", dalle_prompt)

            client = AsyncOpenAI(api_key=openai_key)
            dalle_res = await client.images.generate(
                model="gpt-image-1",
                prompt=dalle_prompt,
                n=1,
                size="1024x1024",
                quality="low",
            )

            image_data = dalle_res.data[0]
            
            storage_dir = os.path.join(os.getcwd(), "public", "reports", "charts")
            os.makedirs(storage_dir, exist_ok=True)

            filename = f"chart_{meeting.id}.png"
            filepath = os.path.join(storage_dir, filename)

            # gpt-image-1 returns base64 by default; dall-e returns url
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                import base64
                img_bytes = base64.b64decode(image_data.b64_json)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                return filepath
            elif hasattr(image_data, 'url') and image_data.url:
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    img_resp = await http_client.get(image_data.url)
                    if img_resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        return filepath

        except Exception as e:
            logger.exception("Failed to generate DALL-E visual for meeting %s: %s", meeting.id, e)
            return None

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

        # 1. Resolve API Keys for DALL-E Visual Generation
        openai_key = None
        if self._api_key_service and meeting.user_id:
            openai_key = await self._api_key_service.get_decrypted_key(meeting.user_id, "openai")
        if not openai_key:
            openai_key = settings.openai_api_key.get_secret_value()

        chart_path = None
        if openai_key:
            chart_path = await self._generate_stats_visual(meeting, openai_key)

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

        # Pass the absolute chart_path to make sure xhtml2pdf can read the image locally
        html_content = template.render(
            meeting=meeting,
            sections=sections,
            chart_path=chart_path,
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

    def _resolve_section_content(self, meeting: Any, section: str) -> str:
        """Map generic report sections to specific agent output sections."""
        outputs = meeting.agent_outputs
        
        # Simple extraction rules based on agent specializations
        if section == "executive_summary":
            return outputs.get("moderator").content if "moderator" in outputs else meeting.pitch_text
        elif section == "market_analysis":
            return outputs.get("market_analyst").content if "market_analyst" in outputs else "Pending analyst review."
        elif section == "mvp_recommendation":
            return outputs.get("product_manager").content if "product_manager" in outputs else "Pending PM review."
        elif section == "revenue_model":
            return outputs.get("finance_advisor").content if "finance_advisor" in outputs else "Pending financial review."
        elif section == "technical_review":
            return outputs.get("technical_architect").content if "technical_architect" in outputs else "Pending technical architect review."
        elif section == "final_recommendation":
            # Combine moderator final remarks
            return outputs.get("moderator").content if "moderator" in outputs else "No recommendation available."
        
        # Fallback to general outputs
        combined = []
        for name, output in outputs.items():
            if section in output.content.lower():
                combined.append(output.content)
        
        return "\n\n".join(combined) if combined else f"Review in-progress by the boardroom."
