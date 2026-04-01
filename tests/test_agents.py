"""Tests for the agent registry and orchestrator."""

import pytest
from backend.agents.registry import get_agent, AGENTS, AgentDefinition


class TestAgentRegistry:
    def test_all_agents_registered(self):
        expected = {"product_owner", "designer", "engineer", "qa", "devops"}
        assert set(AGENTS.keys()) == expected

    def test_get_existing_agent(self):
        agent = get_agent("engineer")
        assert agent.name == "engineer"
        assert agent.title == "Engineer"
        assert "Write" in agent.allowed_tools
        assert "Bash" in agent.allowed_tools

    def test_get_nonexistent_agent_raises(self):
        with pytest.raises(KeyError):
            get_agent("cto")

    def test_engineer_has_full_tools(self):
        agent = get_agent("engineer")
        assert set(agent.allowed_tools) == {"Read", "Write", "Edit", "Bash", "Glob", "Grep"}

    def test_product_owner_has_readonly_tools(self):
        agent = get_agent("product_owner")
        assert "Write" not in agent.allowed_tools
        assert "Bash" not in agent.allowed_tools
        assert "Read" in agent.allowed_tools

    def test_designer_has_readonly_tools(self):
        agent = get_agent("designer")
        assert "Write" not in agent.allowed_tools
        assert "Bash" not in agent.allowed_tools

    def test_all_agents_have_system_prompts(self):
        for name, agent in AGENTS.items():
            assert agent.system_prompt, f"{name} is missing a system prompt"
            assert len(agent.system_prompt) > 50, f"{name} system prompt is too short"

    def test_all_agents_have_titles(self):
        for name, agent in AGENTS.items():
            assert agent.title, f"{name} is missing a title"

    def test_all_agents_have_models(self):
        for name, agent in AGENTS.items():
            assert agent.model, f"{name} is missing a model"

    def test_max_turns_reasonable(self):
        for name, agent in AGENTS.items():
            assert 5 <= agent.max_turns <= 50, f"{name} has unreasonable max_turns: {agent.max_turns}"


class TestAgentDefinition:
    def test_defaults(self):
        agent = AgentDefinition(
            name="test",
            title="Test Agent",
            system_prompt="You are a test.",
            model="claude-haiku-4-5",
        )
        assert agent.allowed_tools == []
        assert agent.max_turns == 25
