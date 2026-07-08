"""
Meeting execution and boardroom orchestration service.
"""

from __future__ import annotations

import time
from datetime import datetime
from uuid import UUID

from app.agents.graph import create_boardroom_graph
from app.core.constants import AGENT_EXECUTION_ORDER, MeetingStatus, estimate_cost
from app.core.logging import get_logger
from app.core.security import generate_thread_id
from app.domain.entities.meeting import AgentOutput, Meeting, MeetingMetrics, TranscriptEntry
from app.domain.exceptions import EntityNotFoundException, InvalidRequestException
from app.domain.interfaces.repositories import IMeetingRepository
from app.infrastructure.cache.redis_cache import redis_cache

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

class ClarificationResult(BaseModel):
    is_ambiguous: bool = Field(description="True if the pitch is missing crucial context")
    questions: list[str] = Field(description="List of 1-3 targeted questions to ask the user")

logger = get_logger(__name__)


class MeetingService:
    """Orchestrates boardroom sessions, graph execution, and metrics calculations."""

    def __init__(
        self,
        meeting_repo: IMeetingRepository,
        checkpointer: Any | None = None,
        search_service: Any | None = None,
        api_key_service: Any | None = None,
    ) -> None:
        self._meeting_repo = meeting_repo
        self._checkpointer = checkpointer
        self._search_service = search_service
        self._api_key_service = api_key_service

    async def create_meeting(self, user_id: UUID, title: str, pitch_text: str) -> Meeting:
        """Create a new boardroom meeting session."""
        if not title or not pitch_text:
            raise InvalidRequestException("Meeting title and startup pitch text are required.")

        meeting_id = UUID(int=time.time_ns())  # Generate a timestamp-based ID or UUID
        import uuid
        m_id = uuid.uuid4()
        thread_id = generate_thread_id(str(m_id))

        meeting = Meeting(
            id=m_id,
            user_id=user_id,
            title=title,
            pitch_text=pitch_text,
            status=MeetingStatus.CREATED,
            thread_id=thread_id,
        )

        return await self._meeting_repo.save(meeting)

    async def clarify_pitch(self, user_id: UUID, title: str, pitch_text: str) -> dict:
        """Analyze a pitch for ambiguity before running the boardroom."""
        if not title or not pitch_text:
            raise InvalidRequestException("Meeting title and startup pitch text are required.")

        openai_key = None
        if self._api_key_service:
            openai_key = await self._api_key_service.get_decrypted_key(user_id, "openai")
        
        if not openai_key:
            # If no API key is available, we can't clarify right now, just return not ambiguous
            return {"is_ambiguous": False, "questions": []}

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0).with_structured_output(ClarificationResult)
        
        prompt = PromptTemplate(
            template="""You are an initial screener for a startup pitch boardroom.
Your job is ONLY to identify CRITICALLY missing context so the boardroom agents have enough information to start their deep analysis. 

For context, the following specialized agents will review this pitch later:
1. Market Analyst: Evaluates market size, competitors, and trends.
2. Product Manager: Evaluates the MVP scope, roadmap, and user acquisition.
3. Finance Advisor: Evaluates unit economics, revenue model, and capital requirements.
4. Technical Architect: Evaluates tech stack feasibility, architecture, and security.

DO NOT ask deep analytical or "grilling" questions (e.g., specific methodologies, complex revenue strategy details, long-term roadmaps, or validation processes) because these specialized Boardroom Agents will do that later.
DO NOT use a rigid checklist. Only mark as ambiguous if the pitch is so vague that it's impossible to understand what the product actually does, who it's for, or how it makes money.
If the pitch provides even a high-level overview of the idea, assume it is sufficient and mark is_ambiguous as false.
If it is truly incomprehensible or missing the most basic premise, mark is_ambiguous as true and ask 1-2 highly specific clarifying questions based ONLY on what is completely missing.

Title: {title}
Pitch: {pitch}""",
            input_variables=["title", "pitch"],
        )
        
        chain = prompt | llm
        try:
            result = await chain.ainvoke({"title": title, "pitch": pitch_text})
            return {"is_ambiguous": result.is_ambiguous, "questions": result.questions}
        except Exception as e:
            logger.error("Failed to clarify pitch: %s", e)
            # Failsafe: return not ambiguous so user can proceed
            return {"is_ambiguous": False, "questions": []}

    async def save_agent_output(self, meeting_or_id: Meeting | UUID, agent_name: str, content: str) -> Meeting:
        """Save intermediate agent output to the database. Accepts loaded Meeting to avoid SELECT round-trip."""
        if isinstance(meeting_or_id, UUID):
            meeting = await self._meeting_repo.get_by_id(meeting_or_id)
            if not meeting:
                raise EntityNotFoundException("Meeting", str(meeting_or_id))
        else:
            meeting = meeting_or_id

        meeting.status = MeetingStatus.IN_PROGRESS

        agent_output = AgentOutput(
            agent_name=agent_name,
            content=content,
        )
        meeting.agent_outputs[agent_name] = agent_output

        # Update transcript
        existing_roles = [t.role for t in meeting.transcript]
        if agent_name not in existing_roles:
            meeting.transcript.append(
                TranscriptEntry(
                    role=agent_name,
                    content=content,
                )
            )
        else:
            for entry in meeting.transcript:
                if entry.role == agent_name:
                    entry.content = content

        return await self._meeting_repo.save(meeting)

    async def execute_boardroom(self, meeting_id: UUID) -> Meeting:
        """
        Run the multi-agent LangGraph courtroom execution.
        """
        meeting = await self._meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise EntityNotFoundException("Meeting", str(meeting_id))

        if meeting.status == MeetingStatus.COMPLETED:
            return meeting

        meeting.status = MeetingStatus.IN_PROGRESS
        await self._meeting_repo.save(meeting)

        # 1. Resolve API Keys
        openai_key = None
        tavily_key = None
        if self._api_key_service and meeting.user_id:
            openai_key = await self._api_key_service.get_decrypted_key(meeting.user_id, "openai")
            tavily_key = await self._api_key_service.get_decrypted_key(meeting.user_id, "tavily")

        # 2. Setup inputs
        inputs = {
            "pitch_text": meeting.pitch_text,
            "user_id": str(meeting.user_id),
            "meeting_id": str(meeting.id),
            "openai_api_key": openai_key or "",
            "tavily_api_key": tavily_key or "",
            "model_name": "gpt-4o",
            "execution_log": [],
            "node_latencies": [],
        }

        config = {"configurable": {"thread_id": meeting.thread_id}}

        # Setup Langfuse callbacks if credentials are configured
        from app.config import get_settings
        settings = get_settings()
        if settings.langfuse_public_key and settings.langfuse_secret_key.get_secret_value():
            from langfuse.langchain import CallbackHandler
            langfuse_handler = CallbackHandler()
            config["callbacks"] = [langfuse_handler]
            config["metadata"] = {
                "langfuse_session_id": str(meeting.id),
                "langfuse_user_id": str(meeting.user_id)
            }

        # 3. Instantiate Graph and execute
        graph = create_boardroom_graph(self._checkpointer)
        
    async def save_boardroom_results(self, meeting_or_id: Meeting | UUID, final_state: dict, openai_key: str | None = None) -> Meeting:
        """
        Parse outputs from a completed graph state and update meeting status to COMPLETED.
        Accepts loaded Meeting to avoid SELECT round-trip.
        """
        if isinstance(meeting_or_id, UUID):
            meeting = await self._meeting_repo.get_by_id(meeting_or_id)
            if not meeting:
                raise EntityNotFoundException("Meeting", str(meeting_or_id))
        else:
            meeting = meeting_or_id

        meeting.status = MeetingStatus.COMPLETED
        meeting.completed_at = datetime.utcnow()

        # Parse agent outputs from final state
        agent_outputs = {}
        for agent_name in AGENT_EXECUTION_ORDER:
            # Resolve specific output keys from State
            state_key = self._get_state_key(agent_name)
            output_content = final_state.get(state_key, "")

            # Extract latency and token usage for this node from execution logs
            prompt_t = 0
            comp_t = 0
            latency = 0.0
            
            # Fetch latency
            latencies = final_state.get("node_latencies", [])
            for lat in latencies:
                if lat.get("node") == agent_name:
                    latency = lat.get("latency_ms", 0.0)

            # Fetch log info
            logs = final_state.get("execution_log", [])
            for log in logs:
                if log.get("agent") == agent_name:
                    prompt_t = log.get("prompt_tokens", 0)
                    comp_t = log.get("completion_tokens", 0)

            agent_outputs[agent_name] = AgentOutput(
                agent_name=agent_name,
                content=output_content,
                tokens_used=prompt_t + comp_t,
                prompt_tokens=prompt_t,
                completion_tokens=comp_t,
                latency_ms=latency,
            )

        meeting.agent_outputs = agent_outputs

        # Calculate aggregated metrics
        total_prompt = final_state.get("prompt_tokens", 0)
        total_comp = final_state.get("completion_tokens", 0)
        total_tokens = total_prompt + total_comp
        
        total_latency = sum(lat.get("latency_ms", 0.0) for lat in final_state.get("node_latencies", []))
        estimated_cost = estimate_cost("gpt-4o", total_prompt, total_comp)

        meeting.metrics = MeetingMetrics(
            total_tokens=total_tokens,
            prompt_tokens=total_prompt,
            completion_tokens=total_comp,
            total_latency_ms=total_latency,
            estimated_cost=estimated_cost,
            agents_completed=len(AGENT_EXECUTION_ORDER),
        )

        # Populate meeting transcript with structured summaries
        transcript = []
        for agent_name in AGENT_EXECUTION_ORDER:
            out = agent_outputs.get(agent_name)
            if out:
                transcript.append(
                    TranscriptEntry(
                        role=agent_name,
                        content=out.content,
                    )
                )
        meeting.transcript = transcript

        # Index meeting vector for semantic searches
        if self._search_service:
            await self._search_service.index_meeting(
                meeting_id=meeting.id,
                title=meeting.title,
                pitch_text=meeting.pitch_text,
                api_key=openai_key,
            )

        # Save meeting updates
        return await self._meeting_repo.save(meeting)

    def _get_state_key(self, agent_name: str) -> str:
        """Map agent name to its output key in BoardroomState."""
        mapping = {
            "moderator": "moderator_output",
            "market_analyst": "market_analysis",
            "product_manager": "product_review",
            "finance_advisor": "financial_analysis",
            "technical_architect": "technical_review",
            "moderator_review": "moderator_review",
        }
        return mapping.get(agent_name, "")
