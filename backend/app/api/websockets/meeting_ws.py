"""
Text-based meeting WebSocket endpoint for streaming courtroom execution events.
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.graph import create_boardroom_graph
from app.core.constants import AGENT_EXECUTION_ORDER, WSEventType
from app.core.logging import get_logger
from app.api.routes.meetings import ANONYMOUS_USER_ID
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.repositories.api_key_repository import ApiKeyRepository
from app.infrastructure.repositories.embedding_repository import EmbeddingRepository
from app.infrastructure.repositories.meeting_repository import MeetingRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.services.api_key_service import ApiKeyService
from app.application.services.meeting_service import MeetingService
from app.application.services.search_service import SearchService

from jose import jwt, JWTError
from app.config import get_settings
from app.domain.entities.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websockets"])


from langchain_core.messages import HumanMessage
import asyncio

async def run_boardroom_execution(
    websocket: WebSocket,
    meeting_id: str,
    meeting_repo: MeetingRepository,
    meeting_service: MeetingService,
    api_key_service: ApiKeyService,
    checkpointer: Any,
) -> None:
    """Helper task to run courtroom graph execution asynchronously."""
    try:
        m_uuid = UUID(meeting_id)
        meeting = await meeting_repo.get_by_id(m_uuid)
        if not meeting:
            await websocket.send_json({
                "type": WSEventType.MEETING_ERROR,
                "error": "Meeting not found.",
            })
            return

        openai_key = await api_key_service.get_decrypted_key(meeting.user_id, "openai")
        tavily_key = await api_key_service.get_decrypted_key(meeting.user_id, "tavily")

        inputs = {
            "pitch_text": meeting.pitch_text,
            "user_id": str(meeting.user_id),
            "meeting_id": str(meeting.id),
            "openai_api_key": openai_key or "",
            "tavily_api_key": tavily_key or "",
            "model_name": "gpt-4o",
            "execution_log": [],
            "node_latencies": [],
        }

        config = {"configurable": {"thread_id": meeting.thread_id}}
        graph = create_boardroom_graph(checkpointer)

        await websocket.send_json({
            "type": WSEventType.MEETING_STARTED,
            "meeting_id": meeting_id,
        })

        # Send agent.started for the first agent (moderator)
        await websocket.send_json({
            "type": WSEventType.AGENT_STARTED,
            "agent": "moderator",
        })

        async for chunk_type, chunk in graph.astream(
            inputs, config=config, stream_mode=["updates", "messages"]
        ):
            if chunk_type == "messages":
                msg, metadata = chunk
                # We only want to stream intermediate messages like tool calls or chunks from active agents
                agent = metadata.get("langgraph_node")
                if agent and msg.content:
                    await websocket.send_json({
                        "type": "agent.message",
                        "agent": agent,
                        "content": msg.content,
                    })
                elif agent and getattr(msg, "tool_calls", None):
                    # Broadcast tool call activity
                    for tc in msg.tool_calls:
                        await websocket.send_json({
                            "type": "agent.activity",
                            "agent": agent,
                            "activity": f"Executing tool: {tc['name']}...",
                        })
                continue
                
            # Handle standard updates
            for node_name, node_output in chunk.items():
                state_key = _get_state_key(node_name)
                if not state_key:
                    continue

                agent_output = node_output.get(state_key, "")
                await websocket.send_json({
                    "type": WSEventType.AGENT_COMPLETED,
                    "agent": node_name,
                    "content": agent_output,
                })

                next_node = None
                if node_name == "moderator":
                    next_node = "market_analyst"
                elif node_name == "market_analyst":
                    next_node = "product_manager"
                elif node_name == "product_manager":
                    next_node = "finance_advisor"
                elif node_name == "finance_advisor":
                    next_node = "technical_architect"
                elif node_name == "technical_architect":
                    next_node = "moderator_review"
                elif node_name == "moderator_review":
                    try:
                        rev_data = json.loads(agent_output)
                        if rev_data.get("decision") == "REVISE":
                            next_node = "market_analyst"
                    except Exception:
                        pass

                if next_node:
                    await websocket.send_json({
                        "type": WSEventType.AGENT_STARTED,
                        "agent": next_node,
                    })

        # Persist and broadcast final metrics
        completed_meeting = await meeting_service.execute_boardroom(m_uuid)
        metrics = completed_meeting.metrics
        await websocket.send_json({
            "type": WSEventType.MEETING_COMPLETED,
            "metrics": metrics.to_dict() if hasattr(metrics, "to_dict") else metrics,
        })
    except Exception as e:
        logger.exception("Error in boardroom execution task: %s", e)
        try:
            await websocket.send_json({
                "type": WSEventType.MEETING_ERROR,
                "error": str(e),
            })
        except Exception:
            pass


@router.websocket("/meeting/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str, token: str | None = None) -> None:
    """
    WebSocket connection to stream LangGraph courtroom execution updates for a pitch.
    Expects JWT token in query parameter '?token=...'
    """
    await websocket.accept()
    logger.info("Text meeting WebSocket connected for meeting %s", meeting_id)

    async for db_session in get_db_session():
        settings = get_settings()
        secret = settings.supabase_jwt_secret.get_secret_value()
        user_id = None
        
        # Authenticate WS connection
        if token and secret:
            try:
                payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
                user_id_str = payload.get("sub")
                if user_id_str:
                    user_id = UUID(user_id_str)
            except JWTError:
                await websocket.send_json({"type": WSEventType.ERROR, "error": "Invalid authentication token."})
                await websocket.close()
                return
        elif settings.is_development:
            from app.api.routes.meetings import ANONYMOUS_USER_ID
            user_id = ANONYMOUS_USER_ID
        else:
            await websocket.send_json({"type": WSEventType.ERROR, "error": "Authentication required."})
            await websocket.close()
            return
            
        # Manually instantiate repositories and services
        meeting_repo = MeetingRepository(db_session)
        
        # Verify ownership
        m_uuid = UUID(meeting_id)
        meeting = await meeting_repo.get_by_id(m_uuid)
        if not meeting or meeting.user_id != user_id:
            await websocket.send_json({"type": WSEventType.ERROR, "error": "Meeting not found or unauthorized."})
            await websocket.close()
            return

        api_key_repo = ApiKeyRepository(db_session)
        embedding_repo = EmbeddingRepository(db_session)

        api_key_service = ApiKeyService(api_key_repo)
        search_service = SearchService(embedding_repo)

        checkpointer = getattr(websocket.app.state, "checkpointer", None)
        meeting_service = MeetingService(
            meeting_repo=meeting_repo,
            checkpointer=checkpointer,
            search_service=search_service,
            api_key_service=api_key_service,
        )

        execution_task = None

        try:
            # Confirm connection to frontend
            await websocket.send_json({
                "type": WSEventType.CONNECTED,
                "meeting_id": meeting_id,
            })

            # Main event loop – wait for commands
            while True:
                data = await websocket.receive_text()
                event = json.loads(data)

                if event.get("action") == "start":
                    if execution_task is None or execution_task.done():
                        execution_task = asyncio.create_task(
                            run_boardroom_execution(
                                websocket=websocket,
                                meeting_id=meeting_id,
                                meeting_repo=meeting_repo,
                                meeting_service=meeting_service,
                                api_key_service=api_key_service,
                                checkpointer=checkpointer,
                            )
                        )
                elif event.get("action") == "interrupt":
                    feedback = event.get("feedback", "")
                    m_uuid = UUID(meeting_id)
                    meeting = await meeting_repo.get_by_id(m_uuid)
                    if meeting:
                        config = {"configurable": {"thread_id": meeting.thread_id}}
                        graph = create_boardroom_graph(checkpointer)
                        
                        # Store HumanMessage into LangGraph thread checkpointer state
                        await graph.aupdate_state(config, {"messages": [HumanMessage(content=feedback)]})
                        logger.info("Steering thread %s with user feedback: %s", meeting.thread_id, feedback)
                        
                        # Broadcast confirmation of interruption back to client
                        await websocket.send_json({
                            "type": WSEventType.AGENT_STARTED,
                            "agent": "user_feedback",
                        })
                        await websocket.send_json({
                            "type": WSEventType.AGENT_COMPLETED,
                            "agent": "user_feedback",
                            "content": json.dumps({"feedback": feedback}),
                        })

        except WebSocketDisconnect:
            logger.info("Text meeting WebSocket disconnected for meeting %s", meeting_id)
            if execution_task and not execution_task.done():
                execution_task.cancel()
            break
        except Exception as e:
            logger.exception("Error in text meeting WebSocket event loop: %s", e)
            if execution_task and not execution_task.done():
                execution_task.cancel()
            try:
                await websocket.send_json({
                    "type": WSEventType.ERROR,
                    "error": str(e),
                })
            except Exception:
                pass
            break


def _get_state_key(agent_name: str) -> str:
    """Map agent node name to the BoardroomState field that holds its output."""
    mapping = {
        "moderator": "moderator_output",
        "market_analyst": "market_analysis",
        "product_manager": "product_review",
        "finance_advisor": "financial_analysis",
        "technical_architect": "technical_review",
        "moderator_review": "moderator_review",
    }
    return mapping.get(agent_name, "")
