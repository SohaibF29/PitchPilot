"""
LangGraph nodes representing boardroom agents.

Includes common execution helper functions.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.state import BoardroomState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def execute_agent_node(
    state: BoardroomState,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    output_key: str,
) -> dict[str, Any]:
    """
    Common helper to run an agent LLM node with retries, logging, and metrics collections.
    """
    start_time = time.time()
    
    # Extract user feedback from messages list
    user_feedback_messages = []
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "human" and msg.content and msg.content != state.get("pitch_text"):
            user_feedback_messages.append(msg.content)
            
    if user_feedback_messages:
        feedback_block = "\n\n### USER INTERRUPTION / STEERING FEEDBACK:\n" + "\n".join(
            f"- {fb}" for fb in user_feedback_messages
        ) + "\n\nIMPORTANT: You MUST incorporate the above user steering/feedback directions into your analysis and findings."
        user_prompt += feedback_block

    # Resolve keys and model
    api_key = state.get("openai_api_key")
    model_name = state.get("model_name", "gpt-4o")
    
    if not api_key:
        # Fallback to backend config if missing from state
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.openai_api_key.get_secret_value()

    # ChatOpenAI client
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        temperature=0.4,
    )

    # 3-attempt tenacity retry policy
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _call_llm() -> Any:
        return await llm.ainvoke([
            SystemMessage(content=system_prompt),
            ("user", user_prompt),
        ])

    retry_count = 0
    try:
        response = await _call_llm()
    except Exception as e:
        logger.exception("LLM call failed for agent '%s': %s", agent_name, e)
        # Update state with failure indicator
        latency_ms = (time.time() - start_time) * 1000
        return {
            "current_agent": agent_name,
            output_key: f'{{"error": "Agent execution failed: {str(e)}"}}',
            "execution_log": [{
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e),
            }],
            "node_latencies": [{"node": agent_name, "latency_ms": latency_ms}],
            "retry_count": 3,
        }

    latency_ms = (time.time() - start_time) * 1000
    
    # Extract tokens from response metadata
    meta = response.response_metadata or {}
    token_usage = meta.get("token_usage", {})
    prompt_tokens = token_usage.get("prompt_tokens", 0)
    completion_tokens = token_usage.get("completion_tokens", 0)
    total_tokens = token_usage.get("total_tokens", 0)

    # Log execution
    logger.info(
        "Agent '%s' complete. Latency: %.2fms. Tokens: %d",
        agent_name,
        latency_ms,
        total_tokens,
    )

    return {
        "current_agent": agent_name,
        output_key: response.content,
        "execution_log": [{
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }],
        "node_latencies": [{"node": agent_name, "latency_ms": latency_ms}],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


async def execute_react_agent_node(
    state: BoardroomState,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    output_key: str,
    tools: list[Any],
) -> dict[str, Any]:
    """
    Common helper to run an iterative ReAct agent sub-graph with tool calling capabilities.
    """
    from langgraph.prebuilt import create_react_agent
    
    start_time = time.time()

    # Extract user feedback from messages list
    user_feedback_messages = []
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "human" and msg.content and msg.content != state.get("pitch_text"):
            user_feedback_messages.append(msg.content)
            
    if user_feedback_messages:
        feedback_block = "\n\n### USER INTERRUPTION / STEERING FEEDBACK:\n" + "\n".join(
            f"- {fb}" for fb in user_feedback_messages
        ) + "\n\nIMPORTANT: You MUST incorporate the above user steering/feedback directions into your research and final report."
        user_prompt += feedback_block
    
    api_key = state.get("openai_api_key")
    model_name = state.get("model_name", "gpt-4o")
    
    if not api_key:
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.openai_api_key.get_secret_value()

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        temperature=0.4,
    )

    react_agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _call_agent() -> dict[str, Any]:
        return await react_agent.ainvoke({"messages": [("user", user_prompt)]})

    retry_count = 0
    try:
        final_state = await _call_agent()
    except Exception as e:
        logger.exception("ReAct sub-graph failed for agent '%s': %s", agent_name, e)
        latency_ms = (time.time() - start_time) * 1000
        return {
            "current_agent": agent_name,
            output_key: f'{{"error": "Agent execution failed: {str(e)}"}}',
            "execution_log": [{
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e),
            }],
            "node_latencies": [{"node": agent_name, "latency_ms": latency_ms}],
            "retry_count": 3,
        }

    latency_ms = (time.time() - start_time) * 1000
    
    # Extract final text output from the last message
    messages = final_state.get("messages", [])
    output_content = messages[-1].content if messages else ""

    # Approximate token tracking (ReAct sub-graphs make multiple calls, we sum the tokens from message metadata if available)
    prompt_tokens = 0
    completion_tokens = 0
    for m in messages:
        if hasattr(m, "response_metadata") and m.response_metadata:
            usage = m.response_metadata.get("token_usage", {})
            prompt_tokens += usage.get("prompt_tokens", 0)
            completion_tokens += usage.get("completion_tokens", 0)
    
    total_tokens = prompt_tokens + completion_tokens

    logger.info(
        "ReAct Agent '%s' complete. Latency: %.2fms. Tokens: %d",
        agent_name,
        latency_ms,
        total_tokens,
    )

    return {
        "current_agent": agent_name,
        output_key: output_content,
        "execution_log": [{
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }],
        "node_latencies": [{"node": agent_name, "latency_ms": latency_ms}],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
