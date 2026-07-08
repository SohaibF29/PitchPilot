"""
Text-based meeting WebSocket endpoint for streaming courtroom execution events.
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.graph import create_boardroom_graph
from app.core.constants import AGENT_EXECUTION_ORDER, WSEventType, MeetingStatus
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
    user_id: UUID,
    checkpointer: Any,
) -> None:
    """Helper task to run courtroom graph execution asynchronously."""
    from app.infrastructure.database.connection import get_db_context
    try:
        async with get_db_context() as db_session:
            meeting_repo = MeetingRepository(db_session)
            api_key_repo = ApiKeyRepository(db_session)
            embedding_repo = EmbeddingRepository(db_session)
            
            api_key_service = ApiKeyService(api_key_repo)
            search_service = SearchService(embedding_repo)
            meeting_service = MeetingService(
                meeting_repo=meeting_repo,
                checkpointer=checkpointer,
                search_service=search_service,
                api_key_service=api_key_service,
            )
            m_uuid = UUID(meeting_id)
            meeting = await meeting_repo.get_by_id(m_uuid)
            if not meeting:
                await websocket.send_json({
                    "type": WSEventType.MEETING_ERROR,
                    "error": "Meeting not found.",
                })
                return
    
            # Fetch both keys in a single DB query instead of two
            user_keys = await api_key_service.get_all_decrypted_keys(meeting.user_id)
            openai_key = user_keys.get("openai")
            tavily_key = user_keys.get("tavily")
    
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
    
            state_wrapper = await graph.aget_state(config)
            # If thread has state, resume by passing None to graph.astream
            graph_inputs = None if state_wrapper.values else inputs
    
            await websocket.send_json({
                "type": WSEventType.MEETING_STARTED,
                "meeting_id": meeting_id,
            })
    
            # Determine the next node to start (works for both initial run and resume)
            next_agent = "moderator"
            for agent in AGENT_EXECUTION_ORDER:
                if agent not in meeting.agent_outputs:
                    next_agent = agent
                    break
    
            await websocket.send_json({
                "type": WSEventType.AGENT_STARTED,
                "agent": next_agent,
            })
    
            async for chunk_type, chunk in graph.astream(
                graph_inputs, config=config, stream_mode=["updates", "messages"]
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
                    
                    # Save incremental agent output to database immediately (passing loaded meeting directly)
                    meeting = await meeting_service.save_agent_output(meeting, node_name, agent_output)
                    await meeting_repo._session.commit()
    
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
                        if "DECISION: REVISE" in agent_output.upper():
                            next_node = "market_analyst"
    
                    if next_node:
                        await websocket.send_json({
                            "type": WSEventType.AGENT_STARTED,
                            "agent": next_node,
                        })
    
            # Fetch the final computed state to persist
            state_wrapper = await graph.aget_state(config)
            final_state = state_wrapper.values
            
            # Persist and broadcast final metrics (passing loaded meeting directly)
            completed_meeting = await meeting_service.save_boardroom_results(meeting, final_state, openai_key)
            await meeting_repo._session.commit() # Commit the transaction immediately so other endpoints see the COMPLETED status
    
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
            from supabase import create_client
            import asyncio
            try:
                supabase_url = settings.supabase_url
                supabase_anon_key = settings.supabase_anon_key.get_secret_value()
                supabase_client = create_client(supabase_url, supabase_anon_key)
                response = await asyncio.to_thread(supabase_client.auth.get_user, token)
                if response and response.user:
                    user_id = UUID(response.user.id)
                else:
                    raise Exception("No user found in token.")
            except Exception as e:
                logger.error(f"WS Auth Error: {e}")
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
                                user_id=user_id,
                                checkpointer=checkpointer,
                            )
                        )
                elif event.get("action") == "stop":
                    if execution_task and not execution_task.done():
                        execution_task.cancel()
                        # Update meeting status to INTERRUPTED
                        m_uuid = UUID(meeting_id)
                        meeting = await meeting_repo.get_by_id(m_uuid)
                        if meeting:
                            meeting.status = MeetingStatus.INTERRUPTED
                            await meeting_repo.save(meeting)
                            await meeting_repo._session.commit()
                        
                        await websocket.send_json({
                            "type": "meeting.interrupted",
                            "meeting_id": meeting_id
                        })
                elif event.get("action") == "restart":
                    try:
                        # Cancel existing task if running
                        if execution_task and not execution_task.done():
                            execution_task.cancel()

                        # Generate new thread_id to wipe checkpoints in LangGraph
                        import uuid
                        new_thread_id = f"thread_{uuid.uuid4()}"

                        m_uuid = UUID(meeting_id)
                        meeting = await meeting_repo.get_by_id(m_uuid)
                        if meeting:
                            meeting.status = MeetingStatus.CREATED
                            meeting.thread_id = new_thread_id
                            meeting.agent_outputs = {}
                            meeting.transcript = []
                            if meeting.metrics:
                                meeting.metrics.agents_completed = 0
                            await meeting_repo.save(meeting)
                            await meeting_repo._session.commit()

                        # Broadcast reset to frontend
                        await websocket.send_json({
                            "type": "meeting.restarted",
                            "meeting_id": meeting_id
                        })

                        # Start executing fresh
                        execution_task = asyncio.create_task(
                            run_boardroom_execution(
                                websocket=websocket,
                                meeting_id=meeting_id,
                                user_id=user_id,
                                checkpointer=checkpointer,
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error during restart: {e}")
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
            
            # Save meeting status as interrupted on disconnect if still in progress
            try:
                m_uuid = UUID(meeting_id)
                meeting = await meeting_repo.get_by_id(m_uuid)
                if meeting and meeting.status == MeetingStatus.IN_PROGRESS:
                    meeting.status = MeetingStatus.INTERRUPTED
                    await meeting_repo.save(meeting)
                    await meeting_repo._session.commit()
            except Exception:
                pass
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
