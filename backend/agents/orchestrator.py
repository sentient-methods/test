"""The Orchestrator — sequences agents and manages the execution pipeline.

This is the brain that takes an ActionableIntent and runs the right agents
in the right order, streaming progress back to the CEO.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import anthropic

from backend.agents.registry import get_agent, AgentDefinition
from backend.chat.models import AgentPhase, AgentStatus, SystemResponse
from backend.chat.session import Session
from backend.config import settings
from backend.intent.translator import ActionableIntent
from backend.middleware.ceo_filter import filter_for_ceo

logger = logging.getLogger(__name__)

# Maps agent names to AgentPhase enum values
PHASE_MAP = {
    "product_owner": AgentPhase.PRODUCT_OWNER,
    "designer": AgentPhase.DESIGNER,
    "engineer": AgentPhase.ENGINEER,
    "qa": AgentPhase.QA,
    "devops": AgentPhase.DEVOPS,
}


async def execute_intent(
    intent: ActionableIntent, session: Session
) -> AsyncIterator[SystemResponse]:
    """Execute an ActionableIntent through the agent pipeline.

    Yields SystemResponse objects that get streamed to the CEO in real time.
    """
    # Sort specs by priority (lower number = higher priority)
    sorted_specs = sorted(intent.specs, key=lambda s: s.priority)

    # Track outputs from each agent for cross-agent context
    agent_outputs: dict[str, str] = {}

    for spec in sorted_specs:
        agent_def = get_agent(spec.agent)
        phase = PHASE_MAP.get(spec.agent, AgentPhase.ENGINEER)

        # Notify CEO that a team is starting work
        yield SystemResponse(
            type="agent_status",
            content=f"{agent_def.title} is on it.",
            agent=phase,
            agent_status=AgentStatus.WORKING,
        )

        # Build context from prior agent outputs (dependency chain)
        prior_context = ""
        for dep in spec.depends_on:
            if dep in agent_outputs:
                prior_context += f"\n--- Output from {dep} ---\n{agent_outputs[dep]}\n"

        # Run the agent
        result = await _run_agent(
            agent_def=agent_def,
            task=spec.task,
            prior_context=prior_context,
            session=session,
            intent=intent,
        )

        agent_outputs[spec.agent] = result

        # Filter result for the CEO (progressive disclosure)
        ceo_summary = await filter_for_ceo(result, agent_def.title, session.detail_level)

        yield SystemResponse(
            type="message",
            content=ceo_summary,
            agent=phase,
            agent_status=AgentStatus.COMPLETE,
            metadata={"raw_output_length": len(result)},
        )

    # Store the execution context in the session for future reference
    session.context["last_intent"] = intent.summary
    session.context["last_outputs"] = {k: v[:500] for k, v in agent_outputs.items()}


async def _run_agent(
    agent_def: AgentDefinition,
    task: str,
    prior_context: str,
    session: Session,
    intent: ActionableIntent,
) -> str:
    """Run a single agent and return its output.

    Uses the Anthropic API directly. When the Claude Agent SDK is available
    and configured, this can be swapped to use `query()` or `ClaudeSDKClient`
    for full tool-use capabilities (file editing, bash, etc.).
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    conversation_context = session.get_conversation_summary()

    prompt = f"""\
CEO's directive: {intent.raw_ceo_input}
Overall plan: {intent.summary}

Your specific task: {task}

{f"Context from other teams:{prior_context}" if prior_context else ""}

{f"Conversation history:{conversation_context}" if conversation_context else ""}

Project directory: {session.project_dir}

Execute your task thoroughly. Be specific and actionable in your output.
"""

    response = await client.messages.create(
        model=agent_def.model,
        max_tokens=4096,
        system=agent_def.system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
