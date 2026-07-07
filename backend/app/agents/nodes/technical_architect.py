"""
Technical Architect agent node implementation.
"""

from __future__ import annotations

from typing import Any

from app.agents.nodes import execute_agent_node
from app.agents.prompts.technical_architect import TECHNICAL_ARCHITECT_SYSTEM_PROMPT
from app.agents.state import BoardroomState


async def technical_architect_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Technical Architect agent logic."""
    pitch = state.get("pitch_text", "")
    moderator_brief = state.get("moderator_output", "")
    market_analysis = state.get("market_analysis", "")
    product_review = state.get("product_review", "")
    financial_analysis = state.get("financial_analysis", "")

    user_prompt = (
        f"Startup Pitch:\n{pitch}\n\n"
        f"Moderator Brief:\n{moderator_brief}\n\n"
        f"Market Analyst Report:\n{market_analysis}\n\n"
        f"Product Manager MVP Scope:\n{product_review}\n\n"
        f"Financial Advisor Runway Review:\n{financial_analysis}\n\n"
        f"Based on the above, design the recommended architecture stack and technical execution review."
    )

    return await execute_agent_node(
        state=state,
        agent_name="technical_architect",
        system_prompt=TECHNICAL_ARCHITECT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="technical_review",
    )
