"""
Product Manager agent node implementation.
"""

from __future__ import annotations

from typing import Any

from app.agents.nodes import execute_react_agent_node
from app.agents.prompts.product_manager import PRODUCT_MANAGER_SYSTEM_PROMPT
from app.agents.state import BoardroomState
from app.agents.tools.search_tool import get_tavily_tool

async def product_manager_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Product Manager agent logic."""
    pitch = state.get("pitch_text", "")
    moderator_brief = state.get("moderator_output", "")
    market_brief = state.get("market_analysis", "")
    tavily_key = state.get("tavily_api_key", "")

    tools = []
    if tavily_key:
        tools.append(get_tavily_tool(tavily_key))

    user_prompt = (
        f"Startup Pitch:\n{pitch}\n\n"
        f"Moderator Brief:\n{moderator_brief}\n\n"
        f"Market Analyst Brief:\n{market_brief}\n\n"
        f"Please execute searches using the search tool to find similar successful or failed products, feature trends, and UX benchmarks. Compile your product and roadmap review."
    )

    return await execute_react_agent_node(
        state=state,
        agent_name="product_manager",
        system_prompt=PRODUCT_MANAGER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="product_review",
        tools=tools,
    )
