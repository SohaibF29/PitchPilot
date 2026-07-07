"""
Application-wide constants for PitchPilot.
"""

from __future__ import annotations

from enum import StrEnum


# ── Agent Names ──────────────────────────────────────────────────

class AgentName(StrEnum):
    """Names of the AI boardroom agents."""
    MODERATOR = "moderator"
    MARKET_ANALYST = "market_analyst"
    PRODUCT_MANAGER = "product_manager"
    FINANCE_ADVISOR = "finance_advisor"
    TECHNICAL_ARCHITECT = "technical_architect"
    MODERATOR_REVIEW = "moderator_review"


# Agent execution order (deterministic pipeline)
AGENT_EXECUTION_ORDER: list[str] = [
    AgentName.MODERATOR,
    AgentName.MARKET_ANALYST,
    AgentName.PRODUCT_MANAGER,
    AgentName.FINANCE_ADVISOR,
    AgentName.TECHNICAL_ARCHITECT,
    AgentName.MODERATOR_REVIEW,
]

# Agent display names for UI
AGENT_DISPLAY_NAMES: dict[str, str] = {
    AgentName.MODERATOR: "Moderator",
    AgentName.MARKET_ANALYST: "Market Analyst",
    AgentName.PRODUCT_MANAGER: "Product Manager",
    AgentName.FINANCE_ADVISOR: "Finance Advisor",
    AgentName.TECHNICAL_ARCHITECT: "Technical Architect",
    AgentName.MODERATOR_REVIEW: "Moderator Review",
}

# Agent descriptions
AGENT_DESCRIPTIONS: dict[str, str] = {
    AgentName.MODERATOR: "Structures the pitch and sets the agenda for the boardroom session.",
    AgentName.MARKET_ANALYST: "Analyzes market size, competition, and growth opportunities.",
    AgentName.PRODUCT_MANAGER: "Evaluates product-market fit, MVP scope, and roadmap feasibility.",
    AgentName.FINANCE_ADVISOR: "Reviews financial models, unit economics, and funding requirements.",
    AgentName.TECHNICAL_ARCHITECT: "Assesses technical feasibility, scalability, and implementation risks.",
    AgentName.MODERATOR_REVIEW: "Reviews all agent findings and decides if further iteration is needed.",
}

# Agent voice assignments for OpenAI Realtime TTS
AGENT_VOICES: dict[str, str] = {
    AgentName.MODERATOR: "sage",
    AgentName.MARKET_ANALYST: "coral",
    AgentName.PRODUCT_MANAGER: "alloy",
    AgentName.FINANCE_ADVISOR: "echo",
    AgentName.TECHNICAL_ARCHITECT: "ash",
}


# ── Meeting Status ───────────────────────────────────────────────

class MeetingStatus(StrEnum):
    """Meeting lifecycle states."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


# ── API Key Providers ────────────────────────────────────────────

class ApiKeyProvider(StrEnum):
    """Supported API key providers."""
    OPENAI = "openai"
    TAVILY = "tavily"


# ── WebSocket Event Types ────────────────────────────────────────

class WSEventType(StrEnum):
    """WebSocket event types for real-time communication."""
    # Meeting events
    MEETING_STARTED = "meeting.started"
    MEETING_COMPLETED = "meeting.completed"
    MEETING_ERROR = "meeting.error"

    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_TOKEN = "agent.token"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"

    # Metrics events
    METRICS_UPDATE = "metrics.update"
    NODE_CHANGE = "node.change"

    # Voice events
    VOICE_CONNECTED = "voice.connected"
    VOICE_TRANSCRIPT = "voice.transcript"
    VOICE_AUDIO = "voice.audio"
    VOICE_INTERRUPTED = "voice.interrupted"
    VOICE_ERROR = "voice.error"

    # System events
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CONNECTED = "connected"


# ── Cost Estimation ──────────────────────────────────────────────

# Pricing per 1M tokens (as of mid-2026)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-4o-realtime-preview": {
        "input_text": 4.00,
        "output_text": 24.00,
        "input_audio": 32.00,
        "output_audio": 64.00,
    },
    "text-embedding-3-small": {
        "input": 0.02,
    },
}


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """
    Estimate the cost of an LLM call.

    Args:
        model: Model name.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * pricing.get("input", 0)
    output_cost = (completion_tokens / 1_000_000) * pricing.get("output", 0)
    return round(input_cost + output_cost, 6)


# ── Report Sections ──────────────────────────────────────────────

REPORT_SECTIONS: list[str] = [
    "executive_summary",
    "swot_analysis",
    "competitive_analysis",
    "risk_assessment",
    "market_analysis",
    "mvp_recommendation",
    "product_roadmap",
    "revenue_model",
    "go_to_market",
    "technical_review",
    "final_recommendation",
]

# ── Embedding ────────────────────────────────────────────────────

EMBEDDING_DIMENSIONS: int = 1536  # text-embedding-3-small
