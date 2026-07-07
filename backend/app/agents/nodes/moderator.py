"""
Moderator agent node implementation.
"""

from __future__ import annotations

from typing import Any

from app.agents.nodes import execute_agent_node
from app.agents.prompts.moderator import MODERATOR_SYSTEM_PROMPT
from app.agents.state import BoardroomState


async def moderator_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Moderator agent logic."""
    pitch = state.get("pitch_text", "")
    
    # We formulate the prompt for the LLM
    user_prompt = f"Here is the startup pitch for you to review and structure:\n\n{pitch}"
    
    return await execute_agent_node(
        state=state,
        agent_name="moderator",
        system_prompt=MODERATOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="moderator_output",
    )
