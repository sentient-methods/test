"""Session management — tracks conversation state and project context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from backend.chat.models import CEOMessage, SystemResponse


@dataclass
class Session:
    """A conversation session between the CEO and MakeItHappen."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[CEOMessage | SystemResponse] = field(default_factory=list)
    project_dir: str = "."
    detail_level: str = "executive"

    # Tracks what agents have produced so far (institutional memory)
    context: dict = field(default_factory=dict)

    def add_ceo_message(self, msg: CEOMessage) -> None:
        self.messages.append(msg)
        if msg.detail_level:
            self.detail_level = msg.detail_level

    def add_system_response(self, resp: SystemResponse) -> None:
        self.messages.append(resp)

    def get_conversation_summary(self) -> str:
        """Produce a compact summary of the conversation for agent context."""
        lines = []
        for msg in self.messages:
            if isinstance(msg, CEOMessage):
                lines.append(f"CEO: {msg.content}")
            elif isinstance(msg, SystemResponse) and msg.type == "message":
                label = msg.agent.value if msg.agent else "system"
                lines.append(f"{label}: {msg.content}")
        return "\n".join(lines[-20:])  # Last 20 exchanges


class SessionStore:
    """In-memory session store. Replace with persistence later."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, project_dir: str = ".") -> Session:
        session = Session(project_dir=project_dir)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None, project_dir: str = ".") -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create(project_dir)


store = SessionStore()
