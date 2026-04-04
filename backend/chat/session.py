"""Session management — tracks conversation state and project context.

Supports both in-memory operation and SQLite persistence.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from backend.chat.models import CEOMessage, SystemResponse


@dataclass
class Session:
    """A conversation session between the CEO and MakeItHappen."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[CEOMessage | SystemResponse] = field(default_factory=list)
    project_dir: str = "."
    detail_level: str = "executive"
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
        return "\n".join(lines[-20:])

    def to_dict(self) -> dict:
        """Serialize session for storage."""
        messages = []
        for msg in self.messages:
            if isinstance(msg, CEOMessage):
                messages.append({"_type": "ceo", **msg.model_dump(mode="json")})
            elif isinstance(msg, SystemResponse):
                messages.append({"_type": "system", **msg.model_dump(mode="json")})
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "project_dir": self.project_dir,
            "detail_level": self.detail_level,
            "context": self.context,
            "messages": messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        """Deserialize session from storage."""
        messages = []
        for msg_data in data.get("messages", []):
            msg_type = msg_data.pop("_type", "system")
            if msg_type == "ceo":
                messages.append(CEOMessage(**msg_data))
            else:
                messages.append(SystemResponse(**msg_data))

        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            messages=messages,
            project_dir=data.get("project_dir", "."),
            detail_level=data.get("detail_level", "executive"),
            context=data.get("context", {}),
        )


class SessionStore:
    """Session store with in-memory cache and SQLite persistence."""

    def __init__(self, db_path: str | None = None) -> None:
        self._sessions: dict[str, Session] = {}
        self._db_path = db_path or str(Path.home() / ".makeitahppen" / "sessions.db")
        self._db_initialized = False

    async def _ensure_db(self) -> None:
        """Lazily initialize the SQLite database."""
        if self._db_initialized:
            return
        try:
            import aiosqlite
            db_dir = Path(self._db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        data TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                await db.commit()
            self._db_initialized = True
        except ImportError:
            self._db_initialized = True  # Run without persistence

    def create(self, project_dir: str = ".") -> Session:
        session = Session(project_dir=project_dir)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> bool:
        """Remove a session from memory and database."""
        removed = session_id in self._sessions
        self._sessions.pop(session_id, None)
        # Note: DB deletion happens async — caller should await _delete_from_db
        return removed

    def get_or_create(self, session_id: str | None, project_dir: str = ".") -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create(project_dir)

    def list_all(self) -> list[Session]:
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    async def save(self, session: Session) -> None:
        """Persist a session to SQLite."""
        self._sessions[session.id] = session
        try:
            await self._ensure_db()
            import aiosqlite
            data = json.dumps(session.to_dict())
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """INSERT INTO sessions (id, created_at, data, updated_at)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at""",
                    (session.id, session.created_at.isoformat(), data, datetime.utcnow().isoformat()),
                )
                await db.commit()
        except ImportError:
            pass  # No aiosqlite, in-memory only

    async def load(self, session_id: str) -> Session | None:
        """Load a session from SQLite."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        try:
            await self._ensure_db()
            import aiosqlite
            async with aiosqlite.connect(self._db_path) as db:
                async with db.execute("SELECT data FROM sessions WHERE id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        session = Session.from_dict(json.loads(row[0]))
                        self._sessions[session.id] = session
                        return session
        except ImportError:
            pass
        return None

    async def load_all(self) -> list[Session]:
        """Load all sessions from SQLite."""
        try:
            await self._ensure_db()
            import aiosqlite
            async with aiosqlite.connect(self._db_path) as db:
                async with db.execute("SELECT data FROM sessions ORDER BY updated_at DESC LIMIT 50") as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        session = Session.from_dict(json.loads(row[0]))
                        if session.id not in self._sessions:
                            self._sessions[session.id] = session
        except ImportError:
            pass
        return self.list_all()


store = SessionStore()
