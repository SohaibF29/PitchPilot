"""
Voice-based meeting WebSocket proxy mapping clients to the OpenAI Realtime API.
"""

from __future__ import annotations

import asyncio
import json
import os
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.client import connect as ws_connect

from app.core.constants import WSEventType
from app.core.logging import get_logger
from app.api.routes.meetings import ANONYMOUS_USER_ID
from app.dependencies import get_api_key_service, get_db_session

logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websockets"])

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"


@router.websocket("/voice/{meeting_id}")
async def voice_websocket_proxy(websocket: WebSocket, meeting_id: str) -> None:
    """
    Bidirectional WebSocket proxy for OpenAI Realtime Voice connections.
    """
    await websocket.accept()
    logger.info("Voice meeting WebSocket proxy connected for meeting %s", meeting_id)

    # 1. Resolve OpenAI API Key
    openai_key = None
    async for db_session in get_db_session():
        api_key_service = await get_api_key_service(get_api_key_repository(db_session))
        openai_key = await api_key_service.get_decrypted_key(ANONYMOUS_USER_ID, "openai")
        break

    if not openai_key:
        # Fallback to env var
        from app.config import get_settings
        settings = get_settings()
        openai_key = settings.openai_api_key.get_secret_value()

    if not openai_key:
        logger.error("No OpenAI API key resolved for voice session %s", meeting_id)
        await websocket.send_json({
            "type": WSEventType.ERROR,
            "error": "Authentication failed: OpenAI key not resolved.",
        })
        await websocket.close()
        return

    # 2. Establish connection to OpenAI Realtime API
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    try:
        async with ws_connect(OPENAI_REALTIME_URL, extra_headers=headers) as openai_ws:
            logger.info("Successfully connected to OpenAI Realtime API for session %s", meeting_id)
            
            # Send voice connected event to client
            await websocket.send_json({
                "type": WSEventType.VOICE_CONNECTED,
                "meeting_id": meeting_id,
            })

            # Define relay loops
            async def client_to_openai_loop() -> None:
                """Relay messages from client browser to OpenAI."""
                try:
                    async for message in websocket.iter_text():
                        # Client can send session updates, audio appends, etc.
                        await openai_ws.send(message)
                except WebSocketDisconnect:
                    logger.info("Client disconnected from voice proxy %s", meeting_id)
                except Exception as e:
                    logger.error("Error in client-to-OpenAI proxy loop: %s", e)

            async def openai_to_client_loop() -> None:
                """Relay messages from OpenAI Realtime to client browser."""
                try:
                    async for message in openai_ws:
                        event = json.loads(message)
                        event_type = event.get("type")

                        # Intercept audio transcripts to build meeting history
                        if event_type == "conversation.item.input_audio_transcription.completed":
                            user_transcript = event.get("transcript", "")
                            logger.info("User audio transcript: %s", user_transcript)
                            # In a production context, save to database
                            await websocket.send_json({
                                "type": WSEventType.VOICE_TRANSCRIPT,
                                "role": "user",
                                "content": user_transcript,
                            })

                        elif event_type == "response.audio_transcript.delta":
                            # Stream back agent TTS text chunk
                            agent_delta = event.get("delta", "")
                            await websocket.send_json({
                                "type": WSEventType.VOICE_TRANSCRIPT,
                                "role": "agent",
                                "content": agent_delta,
                            })

                        # Relay raw event unmodified
                        await websocket.send_text(message)

                except Exception as e:
                    logger.error("Error in OpenAI-to-client proxy loop: %s", e)

            # Run loops concurrently
            await asyncio.gather(
                client_to_openai_loop(),
                openai_to_client_loop(),
            )

    except Exception as e:
        logger.exception("Voice proxy initialization failed for session %s: %s", meeting_id, e)
        await websocket.send_json({
            "type": WSEventType.VOICE_ERROR,
            "error": f"Failed to initialize voice session: {e}",
        })
        try:
            await websocket.close()
        except Exception:
            pass


# Local imports for helper
from app.infrastructure.repositories.api_key_repository import ApiKeyRepository as get_api_key_repository
