"""The Orchestrator — sequences agents and manages the execution pipeline.

This is the brain that takes an ActionableIntent and runs the right agents
in the right order, streaming progress back to the CEO.

SDK agents (Engineer, QA, DevOps) use the Claude Agent SDK with real tool
access — they can edit files, run bash, and search code in a workspace.
Planning agents (ProductOwner, Designer) use the API directly for speed.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import anthropic
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

from backend.agents.registry import get_agent, AgentDefinition
from backend.chat.models import AgentPhase, AgentStatus, SystemResponse
from backend.chat.session import Session
from backend.config import settings
from backend.intent.translator import ActionableIntent
from backend.middleware.ceo_filter import filter_for_ceo
from backend.tools.workspace import ensure_workspace, get_workspace_tree

logger = logging.getLogger(__name__)

PHASE_MAP = {
    "product_owner": AgentPhase.PRODUCT_OWNER,
    "designer": AgentPhase.DESIGNER,
    "engineer": AgentPhase.ENGINEER,
    "qa": AgentPhase.QA,
    "devops": AgentPhase.DEVOPS,
}

# Agents that get real tool access via the Agent SDK
SDK_AGENTS = {"engineer", "qa", "devops"}


async def execute_intent(
    intent: ActionableIntent, session: Session
) -> AsyncIterator[SystemResponse]:
    """Execute an ActionableIntent through the agent pipeline."""
    sorted_specs = sorted(intent.specs, key=lambda s: s.priority)
    agent_outputs: dict[str, str] = {}

    # Ensure this session has a workspace for agents to work in
    workspace = ensure_workspace(session.id)
    session.project_dir = str(workspace)

    for spec in sorted_specs:
        agent_def = get_agent(spec.agent)
        phase = PHASE_MAP.get(spec.agent, AgentPhase.ENGINEER)

        yield SystemResponse(
            type="agent_status",
            content=f"{agent_def.title} is on it.",
            agent=phase,
            agent_status=AgentStatus.WORKING,
        )

        # Build context from prior agent outputs
        prior_context = ""
        for dep in spec.depends_on:
            if dep in agent_outputs:
                prior_context += f"\n--- Output from {dep} ---\n{agent_outputs[dep]}\n"

        # Run the agent
        if spec.agent in SDK_AGENTS:
            result = await _run_sdk_agent(agent_def, spec.task, prior_context, session, intent)
        else:
            result = await _run_api_agent(agent_def, spec.task, prior_context, session, intent)

        agent_outputs[spec.agent] = result

        # Filter for CEO
        ceo_summary = await filter_for_ceo(result, agent_def.title, session.detail_level)

        yield SystemResponse(
            type="message",
            content=ceo_summary,
            agent=phase,
            agent_status=AgentStatus.COMPLETE,
            metadata={"raw_output_length": len(result)},
        )

    session.context["last_intent"] = intent.summary
    session.context["last_outputs"] = {k: v[:500] for k, v in agent_outputs.items()}


def _build_prompt(
    agent_def: AgentDefinition,
    task: str,
    prior_context: str,
    session: Session,
    intent: ActionableIntent,
) -> str:
    """Build the prompt that gets sent to an agent."""
    conversation_context = session.get_conversation_summary()
    workspace_info = get_workspace_tree(session.id)

    return f"""\
CEO's directive: {intent.raw_ceo_input}
Overall plan: {intent.summary}

Your specific task: {task}

{f"Context from other teams:{prior_context}" if prior_context else ""}

{f"Conversation history:{conversation_context}" if conversation_context else ""}

Current workspace state:
{workspace_info}

Project directory: {session.project_dir}

Execute your task thoroughly. Build real, working code.
When creating a project, include all necessary config files (package.json, etc.)
so the project can actually be installed and run.
"""


async def _run_sdk_agent(
    agent_def: AgentDefinition,
    task: str,
    prior_context: str,
    session: Session,
    intent: ActionableIntent,
) -> str:
    """Run an agent using the Claude Agent SDK with real tool access.

    The agent can read/write files, run bash commands, search code, etc.
    in the session's workspace directory.
    """
    prompt = _build_prompt(agent_def, task, prior_context, session, intent)
    result_parts: list[str] = []

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=session.project_dir,
                allowed_tools=agent_def.allowed_tools,
                system_prompt=agent_def.system_prompt,
                permission_mode="bypassPermissions",
                max_turns=agent_def.max_turns,
                model=agent_def.model,
            ),
        ):
            if isinstance(message, ResultMessage):
                result_parts.append(message.result)
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_parts.append(block.text)
    except Exception as e:
        logger.exception("SDK agent %s failed", agent_def.name)
        return f"Agent {agent_def.title} encountered an error: {e}"

    return "\n".join(result_parts) if result_parts else "Task completed."


async def _run_api_agent(
    agent_def: AgentDefinition,
    task: str,
    prior_context: str,
    session: Session,
    intent: ActionableIntent,
) -> str:
    """Run a planning-only agent via the Anthropic API directly.

    Used for agents that don't need tool access (ProductOwner, Designer).
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(agent_def, task, prior_context, session, intent)

    response = await client.messages.create(
        model=agent_def.model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=agent_def.system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    return next(
        (block.text for block in response.content if block.type == "text"),
        "Task completed.",
    )
