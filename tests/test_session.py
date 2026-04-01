"""Tests for session management."""

import json
from backend.chat.models import CEOMessage, SystemResponse, AgentPhase, AgentStatus
from backend.chat.session import Session, SessionStore


class TestSession:
    def test_create_session(self):
        session = Session()
        assert session.id
        assert len(session.messages) == 0
        assert session.detail_level == "executive"

    def test_add_messages(self):
        session = Session()
        session.add_ceo_message(CEOMessage(content="Build me an app"))
        session.add_system_response(SystemResponse(
            type="message",
            content="On it.",
            agent=AgentPhase.CHIEF_OF_STAFF,
            agent_status=AgentStatus.WORKING,
        ))
        assert len(session.messages) == 2

    def test_detail_level_updates(self):
        session = Session()
        session.add_ceo_message(CEOMessage(content="x", detail_level="technical"))
        assert session.detail_level == "technical"

    def test_conversation_summary(self):
        session = Session()
        session.add_ceo_message(CEOMessage(content="Build a landing page"))
        summary = session.get_conversation_summary()
        assert "Build a landing page" in summary

    def test_conversation_summary_limits(self):
        session = Session()
        for i in range(30):
            session.add_ceo_message(CEOMessage(content=f"Message {i}"))
        summary = session.get_conversation_summary()
        assert "Message 10" in summary
        assert "Message 0" not in summary  # Old messages trimmed

    def test_serialization_roundtrip(self):
        session = Session(project_dir="/tmp/test")
        session.add_ceo_message(CEOMessage(content="Build an app"))
        session.add_system_response(SystemResponse(
            type="message",
            content="Done.",
            agent=AgentPhase.ENGINEER,
            agent_status=AgentStatus.COMPLETE,
        ))
        session.context["last_intent"] = "Build an app"

        data = session.to_dict()
        restored = Session.from_dict(data)

        assert restored.id == session.id
        assert restored.project_dir == "/tmp/test"
        assert len(restored.messages) == 2
        assert restored.context["last_intent"] == "Build an app"

    def test_serialization_json_safe(self):
        session = Session()
        session.add_ceo_message(CEOMessage(content="test"))
        data = session.to_dict()
        json_str = json.dumps(data)
        assert json_str  # No serialization errors


class TestSessionStore:
    def test_create_and_get(self):
        store = SessionStore()
        session = store.create()
        retrieved = store.get(session.id)
        assert retrieved is session

    def test_get_or_create_new(self):
        store = SessionStore()
        session = store.get_or_create(None)
        assert session.id

    def test_get_or_create_existing(self):
        store = SessionStore()
        s1 = store.create()
        s2 = store.get_or_create(s1.id)
        assert s1 is s2

    def test_list_all(self):
        store = SessionStore()
        store.create()
        store.create()
        sessions = store.list_all()
        assert len(sessions) == 2

    def test_get_nonexistent(self):
        store = SessionStore()
        assert store.get("nonexistent") is None
