"""WebSocket and REST endpoints for the CEO chat interface."""

from __future__ import annotations

import json
import logging
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.chat.models import AgentPhase, AgentStatus, CEOMessage, SystemResponse
from backend.chat.session import store
from backend.intent.translator import translate_intent
from backend.agents.orchestrator import execute_intent
from backend.middleware.progressive_disclosure import detect_detail_level

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/chat")
async def chat_websocket(websocket: WebSocket):
    """Main chat endpoint. The CEO connects here.

    Protocol:
        CEO sends: {"content": "...", "session_id": "...", "detail_level": "executive"}
        System streams back: SystemResponse objects as JSON
    """
    await websocket.accept()
    session = None

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            ceo_msg = CEOMessage(**data)

            # Get or create session
            session = store.get_or_create(ceo_msg.session_id)
            session.add_ceo_message(ceo_msg)

            # Check if CEO is adjusting detail level
            new_level = detect_detail_level(ceo_msg.content)
            if new_level:
                session.detail_level = new_level

            # Acknowledge receipt
            await _send(websocket, SystemResponse(
                type="agent_status",
                content="On it, CEO.",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.THINKING,
                metadata={"session_id": session.id},
            ))

            # Phase 1: Translate CEO intent
            try:
                intent = await translate_intent(ceo_msg.content, session)
            except Exception as e:
                logger.exception("Intent translation failed")
                await _send(websocket, SystemResponse(
                    type="message",
                    content=f"I had trouble understanding that. Could you rephrase? ({e})",
                    agent=AgentPhase.CHIEF_OF_STAFF,
                    agent_status=AgentStatus.BLOCKED,
                ))
                await _send(websocket, SystemResponse(type="done", content=""))
                continue

            # If clarifications are needed, ask the CEO and re-enable input
            if intent.clarifications_needed:
                await _send(websocket, SystemResponse(
                    type="clarification",
                    content="\n".join(intent.clarifications_needed),
                    agent=AgentPhase.CHIEF_OF_STAFF,
                    agent_status=AgentStatus.BLOCKED,
                    metadata={"intent_summary": intent.summary},
                ))
                await _send(websocket, SystemResponse(
                    type="done",
                    content="",
                    agent=AgentPhase.CHIEF_OF_STAFF,
                    agent_status=AgentStatus.COMPLETE,
                ))
                continue

            # Notify CEO of the plan
            await _send(websocket, SystemResponse(
                type="message",
                content=f"Plan: {intent.summary} (complexity: {intent.complexity})",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.WORKING,
            ))

            # Phase 2: Execute through the agent pipeline
            try:
                async for update in execute_intent(intent, session):
                    session.add_system_response(update)
                    await _send(websocket, update)
            except Exception as e:
                logger.exception("Execution failed")
                await _send(websocket, SystemResponse(
                    type="message",
                    content=f"Hit a snag during execution: {e}. Want me to try a different approach?",
                    agent=AgentPhase.CHIEF_OF_STAFF,
                    agent_status=AgentStatus.BLOCKED,
                ))
                await _send(websocket, SystemResponse(type="done", content=""))
                continue

            # Done
            await _send(websocket, SystemResponse(
                type="done",
                content="As you wish, CEO. What's next?",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.COMPLETE,
            ))

            # Persist session
            await store.save(session)

    except WebSocketDisconnect:
        logger.info("CEO disconnected (session=%s)", session.id if session else "none")
    except Exception:
        logger.exception("Unexpected error in chat session")
        try:
            await _send(websocket, SystemResponse(
                type="message",
                content="Something unexpected happened. Reconnect and I'll pick up where we left off.",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.BLOCKED,
            ))
        except Exception:
            pass


@router.get("/sessions")
async def list_sessions():
    """List all sessions for the CEO."""
    sessions = store.list_all()
    return JSONResponse([
        {
            "id": s.id,
            "created_at": s.created_at.isoformat(),
            "message_count": len(s.messages),
            "last_intent": s.context.get("last_intent", ""),
        }
        for s in sessions
    ])


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session's messages."""
    session = store.get(session_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return JSONResponse({
        "id": session.id,
        "created_at": session.created_at.isoformat(),
        "detail_level": session.detail_level,
        "messages": [
            msg.model_dump(mode="json") if hasattr(msg, "model_dump") else {"content": str(msg)}
            for msg in session.messages
        ],
    })


async def _send(websocket: WebSocket, response: SystemResponse) -> None:
    await websocket.send_text(response.model_dump_json())
