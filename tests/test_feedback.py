"""Tests for the feedback queue."""

from backend.tools.feedback import FeedbackQueue, FeedbackPriority


class TestFeedbackQueue:
    def test_add_item(self):
        q = FeedbackQueue()
        item = q.add(agent="engineer", question="Which database?")
        assert item.id == "fb-1"
        assert item.agent == "engineer"
        assert not item.resolved

    def test_multiple_items(self):
        q = FeedbackQueue()
        q.add(agent="engineer", question="Q1")
        q.add(agent="designer", question="Q2")
        assert len(q.pending()) == 2

    def test_resolve(self):
        q = FeedbackQueue()
        item = q.add(agent="engineer", question="Which database?", options=["Postgres", "SQLite"])
        q.resolve(item.id, "Postgres")
        assert len(q.pending()) == 0
        assert item.resolved
        assert item.answer == "Postgres"

    def test_resolve_nonexistent(self):
        q = FeedbackQueue()
        result = q.resolve("nonexistent", "answer")
        assert result is None

    def test_format_for_ceo(self):
        q = FeedbackQueue()
        q.add(agent="engineer", question="Which database should we use?", options=["Postgres", "SQLite"])
        output = q.format_for_ceo()
        assert "Which database" in output
        assert "Postgres" in output

    def test_format_empty(self):
        q = FeedbackQueue()
        assert q.format_for_ceo() == ""

    def test_priority(self):
        q = FeedbackQueue()
        q.add(agent="engineer", question="Critical", priority=FeedbackPriority.CRITICAL)
        item = q.pending()[0]
        assert item.priority == FeedbackPriority.CRITICAL
