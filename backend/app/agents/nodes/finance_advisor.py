"""
Finance Advisor agent node implementation.
"""

from __future__ import annotations

from typing import Any

from app.agents.nodes import execute_react_agent_node
from app.agents.prompts.finance_advisor import FINANCE_ADVISOR_SYSTEM_PROMPT
from app.agents.state import BoardroomState
from app.agents.tools.calculator_tool import calculate_saas_metrics
from app.agents.tools.search_tool import get_tavily_tool

async def finance_advisor_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Finance Advisor agent logic."""
    pitch = state.get("pitch_text", "")
    moderator_brief = state.get("moderator_output", "")
    market_analysis = state.get("market_analysis", "")
    product_review = state.get("product_review", "")
    tavily_key = state.get("tavily_api_key", "")

    tools = []
    if tavily_key:
        tools.append(get_tavily_tool(tavily_key))

    saas_calcs = calculate_saas_metrics(arpu=49.0, churn_rate=0.03, cac=250.0)

    user_prompt = (
        f"Startup Pitch:\n{pitch}\n\n"
        f"Moderator Brief:\n{moderator_brief}\n\n"
        f"Market Analyst Report:\n{market_analysis}\n\n"
        f"Product Manager MVP Scope:\n{product_review}\n\n"
        f"Baseline SaaS Economics Baseline Reference (CAC/LTV): {saas_calcs}\n\n"
        f"Please execute searches using the search tool to find current financial benchmarks, funding rounds of competitors, and valuation metrics in this sector. Then, analyze the business model, unit economics, and funding plan."
    )

    return await execute_react_agent_node(
        state=state,
        agent_name="finance_advisor",
        system_prompt=FINANCE_ADVISOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="financial_analysis",
        tools=tools,
    )
