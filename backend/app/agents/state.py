"""
LangGraph state schema for PitchPilot boardroom.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class BoardroomState(TypedDict):
    """State schema for the PitchPilot boardroom LangGraph."""

    # Thread messages list (using langchain's add_messages reducer)
    messages: Annotated[list[AnyMessage], add_messages]

    # Startup idea context
    pitch_text: str
    user_id: str
    meeting_id: str

    # Agent outputs (persisted on execution complete)
    moderator_output: str  # Structured JSON string
    market_analysis: str   # Structured JSON string
    product_review: str    # Structured JSON string
    financial_analysis: str  # Structured JSON string
    technical_review: str  # Structured JSON string
    moderator_review: str  # Moderator's review decision (e.g. "APPROVED" or "REVISE")

    # Flow control and tracking
    current_agent: str
    iteration_count: Annotated[int, operator.add]
    execution_log: Annotated[list[dict[str, Any]], operator.add]

    # Metrics
    total_tokens: Annotated[int, operator.add]
    prompt_tokens: Annotated[int, operator.add]
    completion_tokens: Annotated[int, operator.add]
    retry_count: Annotated[int, operator.add]
    node_latencies: Annotated[list[dict[str, Any]], operator.add]

    # Keys resolved during execution
    tavily_api_key: str
    openai_api_key: str
    model_name: str
