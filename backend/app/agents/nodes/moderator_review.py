from typing import Any
from app.agents.nodes import execute_agent_node
from app.agents.state import BoardroomState

MODERATOR_REVIEW_SYSTEM_PROMPT = """
You are the Moderator of the AI Boardroom.
Review the compiled reports from the Market Analyst, Product Manager, Finance Advisor, and Technical Architect.
If the reports are comprehensive, deep, and diverse, output a JSON object:
{ "decision": "APPROVED", "reason": "Reports are robust." }

If the reports lack depth (e.g. missing competitors, shallow financial models, lacking specific benchmarks), output a JSON object:
{ "decision": "REVISE", "reason": "Missing deep competitive analysis, please revise." }

Always output valid JSON.
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
