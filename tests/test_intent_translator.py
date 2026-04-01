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

    def test_plan_pipeline(self):
        intent = _fallback_intent("plan", "Let's think about the architecture")
        agents = [s.agent for s in intent.specs]
        assert agents == ["product_owner", "designer"]

    def test_change_pipeline(self):
        intent = _fallback_intent("change", "Make the header blue")
        agents = [s.agent for s in intent.specs]
        assert agents == ["engineer", "qa"]

    def test_unknown_type_defaults_to_engineer(self):
        intent = _fallback_intent("unknown_type", "Something")
        agents = [s.agent for s in intent.specs]
        assert agents == ["engineer"]

    def test_priorities_are_sequential(self):
        intent = _fallback_intent("build", "Build something")
        priorities = [s.priority for s in intent.specs]
        assert priorities == [1, 2, 3, 4]

    def test_raw_ceo_input_preserved(self):
        intent = _fallback_intent("build", "Build me a rocket ship")
        assert intent.raw_ceo_input == "Build me a rocket ship"


class TestDetailLevelDetection:
    def test_escalate_to_technical(self):
        assert detect_detail_level("Show me the code") == "technical"
        assert detect_detail_level("Give me technical details") == "technical"
        assert detect_detail_level("Show me everything") == "technical"
        assert detect_detail_level("I want to debug this") == "technical"

    def test_escalate_to_manager(self):
        assert detect_detail_level("Tell me more about that") == "manager"
        assert detect_detail_level("Can you elaborate?") == "manager"
        assert detect_detail_level("What decisions were made?") == "manager"
        assert detect_detail_level("Show me more") == "manager"

    def test_deescalate_to_executive(self):
        assert detect_detail_level("Just the bottom line") == "executive"
        assert detect_detail_level("Keep it simple") == "executive"
        assert detect_detail_level("Give me the summary") == "executive"
        assert detect_detail_level("Just the highlights please") == "executive"

    def test_no_change(self):
        assert detect_detail_level("Build me a todo app") is None
        assert detect_detail_level("Make the header blue") is None
        assert detect_detail_level("Hello") is None

    def test_case_insensitive(self):
        assert detect_detail_level("SHOW ME THE CODE") == "technical"
        assert detect_detail_level("Tell Me More") == "manager"


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

    def test_agent_spec_defaults(self):
        spec = AgentSpec(agent="engineer", task="Do something")
        assert spec.depends_on == []
        assert spec.priority == 1
