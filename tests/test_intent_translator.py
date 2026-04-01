"""Tests for the intent translation layer."""

from backend.intent.translator import ActionableIntent, AgentSpec, _fallback_intent
from backend.middleware.progressive_disclosure import detect_detail_level


class TestFallbackIntent:
    def test_build_pipeline(self):
        intent = _fallback_intent("build", "Make me a landing page")
        assert intent.type == "build"
        agents = [s.agent for s in intent.specs]
        assert agents == ["product_owner", "designer", "engineer", "qa"]

    def test_fix_pipeline(self):
        intent = _fallback_intent("fix", "The button is broken")
        assert intent.type == "fix"
        agents = [s.agent for s in intent.specs]
        assert agents == ["engineer", "qa"]

    def test_deploy_pipeline(self):
        intent = _fallback_intent("deploy", "Ship it")
        agents = [s.agent for s in intent.specs]
        assert agents == ["devops"]

    def test_explain_pipeline(self):
        intent = _fallback_intent("explain", "What does our app do?")
        agents = [s.agent for s in intent.specs]
        assert agents == ["product_owner"]

    def test_priorities_are_sequential(self):
        intent = _fallback_intent("build", "Build something")
        priorities = [s.priority for s in intent.specs]
        assert priorities == [1, 2, 3, 4]


class TestDetailLevelDetection:
    def test_escalate_to_technical(self):
        assert detect_detail_level("Show me the code") == "technical"
        assert detect_detail_level("Give me technical details") == "technical"

    def test_escalate_to_manager(self):
        assert detect_detail_level("Tell me more about that") == "manager"
        assert detect_detail_level("Can you elaborate?") == "manager"

    def test_deescalate_to_executive(self):
        assert detect_detail_level("Just the bottom line") == "executive"
        assert detect_detail_level("Keep it simple") == "executive"

    def test_no_change(self):
        assert detect_detail_level("Build me a todo app") is None


class TestActionableIntent:
    def test_has_clarifications(self):
        intent = ActionableIntent(
            type="build",
            summary="Something",
            complexity="moderate",
            clarifications_needed=["What color?"],
        )
        assert intent.clarifications_needed
        assert not intent.specs

    def test_ready_to_execute(self):
        intent = ActionableIntent(
            type="build",
            summary="Landing page",
            complexity="simple",
            specs=[AgentSpec(agent="engineer", task="Build it")],
        )
        assert intent.specs
        assert not intent.clarifications_needed
