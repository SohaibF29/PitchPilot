"""
LangGraph graph orchestrator for the PitchPilot AI boardroom.
"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents.nodes.finance_advisor import finance_advisor_node
from app.agents.nodes.market_analyst import market_analyst_node
from app.agents.nodes.moderator import moderator_node
from app.agents.nodes.product_manager import product_manager_node
from app.agents.nodes.technical_architect import technical_architect_node
from app.agents.state import BoardroomState


def create_boardroom_graph(checkpointer: BaseCheckpointSaver | None = None) -> Any:
    """
    Constructs and compiles the deterministic multi-agent boardroom graph.

    Execution Flow:
    START -> Moderator -> Market Analyst -> Product Manager -> Finance Advisor -> Technical Architect -> END
    """
    workflow = StateGraph(BoardroomState)

    # 1. Register Nodes
    workflow.add_node("moderator", moderator_node)
    workflow.add_node("market_analyst", market_analyst_node)
    workflow.add_node("product_manager", product_manager_node)
    workflow.add_node("finance_advisor", finance_advisor_node)
    workflow.add_node("technical_architect", technical_architect_node)

    import json
    from app.agents.nodes.moderator_review import moderator_review_node

    workflow.add_node("moderator_review", moderator_review_node)

    # 2. Register Edges (Iterative flow)
    workflow.add_edge(START, "moderator")
    workflow.add_edge("moderator", "market_analyst")
    workflow.add_edge("market_analyst", "product_manager")
    workflow.add_edge("product_manager", "finance_advisor")
    workflow.add_edge("finance_advisor", "technical_architect")
    workflow.add_edge("technical_architect", "moderator_review")

    def review_condition(state: BoardroomState) -> str:
        iters = state.get("iteration_count", 0)
        if iters >= 2:
            return END
        
        review = state.get("moderator_review", "")
        if "DECISION: REVISE" in review.upper():
            return "market_analyst"
        return END

    workflow.add_conditional_edges(
        "moderator_review",
        review_condition,
        {
            "market_analyst": "market_analyst",
            END: END
        }
    )

    # 3. Compile Graph with persistence
    # If no checkpointer is provided (e.g. dev/test), compile without checkpointing
    return workflow.compile(checkpointer=checkpointer)
