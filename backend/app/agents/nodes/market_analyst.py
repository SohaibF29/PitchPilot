"""
Market Analyst agent node implementation.
"""

from __future__ import annotations

from typing import Any

from app.agents.nodes import execute_react_agent_node
from app.agents.prompts.market_analyst import MARKET_ANALYST_SYSTEM_PROMPT
from app.agents.state import BoardroomState
from app.agents.tools.search_tool import get_tavily_tool

async def market_analyst_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Market Analyst agent logic."""
    pitch = state.get("pitch_text", "")
    moderator_brief = state.get("moderator_output", "")
    tavily_key = state.get("tavily_api_key", "")

    tools = []
    if tavily_key:
        tools.append(get_tavily_tool(tavily_key))

    user_prompt = (
        f"Startup Pitch:\n{pitch}\n\n"
        f"Moderator Brief:\n{moderator_brief}\n\n"
        f"Please execute 2-3 diverse searches using the search tool to compile an in-depth market report. Search for competitors, TAM/SAM/SOM, and industry trends."
    )

    return await execute_react_agent_node(
        state=state,
        agent_name="market_analyst",
        system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="market_analysis",
        tools=tools,
    )
