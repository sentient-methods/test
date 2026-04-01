"""WebSocket and REST endpoints for the CEO chat interface."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.chat.models import AgentPhase, AgentStatus, CEOMessage, SystemResponse
from backend.chat.session import store
from backend.intent.translator import translate_intent
from backend.agents.orchestrator import execute_intent

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

            # Acknowledge receipt
            await _send(websocket, SystemResponse(
                type="agent_status",
                content="On it, CEO.",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.THINKING,
                metadata={"session_id": session.id},
            ))

            # Phase 1: Translate CEO intent
            intent = await translate_intent(ceo_msg.content, session)

            # If clarifications are needed, ask the CEO
            if intent.clarifications_needed:
                await _send(websocket, SystemResponse(
                    type="clarification",
                    content="\n".join(intent.clarifications_needed),
                    agent=AgentPhase.CHIEF_OF_STAFF,
                    agent_status=AgentStatus.BLOCKED,
                    metadata={"intent_summary": intent.summary},
                ))
                continue

            # Phase 2: Execute through the agent pipeline
            async for update in execute_intent(intent, session):
                await _send(websocket, update)

            # Done
            await _send(websocket, SystemResponse(
                type="done",
                content="Done, CEO. What's next?",
                agent=AgentPhase.CHIEF_OF_STAFF,
                agent_status=AgentStatus.COMPLETE,
            ))

    except WebSocketDisconnect:
        logger.info("CEO disconnected (session=%s)", session.id if session else "none")
    except Exception as e:
        logger.exception("Error in chat session")
        await _send(websocket, SystemResponse(
            type="message",
            content=f"Hit a snag: {e}. Want me to try a different approach?",
            agent=AgentPhase.CHIEF_OF_STAFF,
            agent_status=AgentStatus.BLOCKED,
        ))


async def _send(websocket: WebSocket, response: SystemResponse) -> None:
    await websocket.send_text(response.model_dump_json())
