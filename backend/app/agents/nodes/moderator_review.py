from typing import Any
from app.agents.nodes import execute_agent_node
from app.agents.state import BoardroomState

MODERATOR_REVIEW_SYSTEM_PROMPT = """
You are the Moderator of the AI Boardroom.
Your objective is to critically evaluate the compiled reports from the Market Analyst, Product Manager, Finance Advisor, and Technical Architect.
Assess whether the reports deeply analyze the specific startup pitch provided, if they identify critical vulnerabilities, and if they offer actionable, specific insights rather than generic advice.

Rules for evaluation:
1. If ANY report contains mostly generic statements, lacks specific market data, fails to identify critical risks, or misses obvious flaws in the pitch, output:
DECISION: REVISE
REASON: <Specify EXACTLY which agent needs to improve and what specific gaps they must address in the next iteration.>

2. If the pitch is highly complex but the reports are surface-level, you must demand a REVISE.

3. If AND ONLY IF all reports are highly specific, data-driven, deeply critical, and provide a comprehensive 360-degree view of the startup's viability, output:
DECISION: APPROVED
REASON: <Summarize why the reports meet the high standard of the boardroom.>

Be strict. Do not approve mediocre or generic analysis. 
IMPORTANT: YOUR OUTPUT MUST BE IN PLAIN MARKDOWN TEXT. DO NOT USE JSON. DO NOT WRAP YOUR RESPONSE IN A JSON BLOCK.
"""

async def moderator_review_node(state: BoardroomState) -> dict[str, Any]:
    """Execute the Moderator Review agent logic to critique and potentially loop."""
    pitch = state.get("pitch_text", "")
    reports = (
        f"Market Analysis: {state.get('market_analysis', '')}\n\n"
        f"Product Review: {state.get('product_review', '')}\n\n"
        f"Financial Analysis: {state.get('financial_analysis', '')}\n\n"
        f"Technical Review: {state.get('technical_review', '')}\n"
    )

    user_prompt = (
        f"Startup Pitch:\n{pitch}\n\n"
        f"Compiled Reports:\n{reports}\n\n"
        f"Provide your review decision."
    )

    # Increment iteration count
    current_iters = state.get("iteration_count", 0)

    # We use execute_agent_node since this is just a quick JSON critique
    result = await execute_agent_node(
        state=state,
        agent_name="moderator_review",
        system_prompt=MODERATOR_REVIEW_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_key="moderator_review",
    )
    result["iteration_count"] = 1
    return result
