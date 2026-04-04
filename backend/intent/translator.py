"""Translates CEO-speak into actionable specs for the agent pipeline."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import anthropic

from backend.config import settings
from backend.intent.prompts import CLASSIFIER_PROMPT, TRANSLATOR_PROMPT
from backend.tools.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)


@dataclass
class AgentSpec:
    """A task assignment for one functional team."""
    agent: str
    task: str
    depends_on: list[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class ActionableIntent:
    """The translated output — CEO vision turned into executable specs."""
    type: str  # build, fix, change, deploy, explain, plan
    summary: str
    complexity: str  # trivial, simple, moderate, complex
    specs: list[AgentSpec] = field(default_factory=list)
    clarifications_needed: list[str] = field(default_factory=list)
    raw_ceo_input: str = ""


async def classify_intent(ceo_input: str, session_id: str = "") -> str:
    """Fast classification of what the CEO wants (uses Haiku for speed)."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.model_classifier,
        max_tokens=20,
        system=CLASSIFIER_PROMPT,
        messages=[{"role": "user", "content": ceo_input}],
    )
    if session_id:
        cost_tracker.track(session_id, "classifier", settings.model_classifier,
                           response.usage.input_tokens, response.usage.output_tokens)
    intent_type = response.content[0].text.strip().lower()
    valid_types = {"build", "fix", "change", "deploy", "explain", "plan"}
    return intent_type if intent_type in valid_types else "build"


async def translate_intent(ceo_input: str, session) -> ActionableIntent:
    """Full translation of CEO directive into actionable specs.

    This is the Chief of Staff doing their job — understanding the CEO,
    understanding the org's capabilities, and producing a clear plan.
    """
    # Step 1: Classify (fast, cheap)
    session_id = session.id if hasattr(session, "id") else ""
    intent_type = await classify_intent(ceo_input, session_id)
    logger.info("Classified intent: %s", intent_type)

    # Step 2: Translate into specs (more thorough)
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    context = session.get_conversation_summary() if session.messages else "New project, no prior context."

    response = await client.messages.create(
        model=settings.model_translator,
        max_tokens=2000,
        system=TRANSLATOR_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"CEO's directive: {ceo_input}\n\n"
                    f"Conversation context:\n{context}\n\n"
                    f"Initial classification: {intent_type}\n\n"
                    "Translate this into actionable specs."
                ),
            }
        ],
    )

    if session_id:
        cost_tracker.track(session_id, "translator", settings.model_translator,
                           response.usage.input_tokens, response.usage.output_tokens)

    raw_text = response.content[0].text.strip()

    try:
        # Extract JSON from response (handle markdown code blocks)
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        data = json.loads(raw_text)
        specs = [AgentSpec(**s) for s in data.get("specs", [])]

        return ActionableIntent(
            type=data.get("type", intent_type),
            summary=data.get("summary", ceo_input),
            complexity=data.get("complexity", "moderate"),
            specs=specs,
            clarifications_needed=data.get("clarifications_needed", []),
            raw_ceo_input=ceo_input,
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to parse translator output: %s — falling back", e)
        # Fallback: create a reasonable default based on classification
        return _fallback_intent(intent_type, ceo_input)


def _fallback_intent(intent_type: str, ceo_input: str) -> ActionableIntent:
    """When translation fails, produce a sensible default pipeline."""
    pipelines = {
        "build": ["product_owner", "designer", "engineer", "qa"],
        "fix": ["engineer", "qa"],
        "change": ["engineer", "qa"],
        "deploy": ["devops"],
        "explain": ["product_owner"],
        "plan": ["product_owner", "designer"],
    }
    agents = pipelines.get(intent_type, ["engineer"])
    specs = [AgentSpec(agent=a, task=ceo_input, priority=i + 1) for i, a in enumerate(agents)]

    return ActionableIntent(
        type=intent_type,
        summary=ceo_input,
        complexity="moderate",
        specs=specs,
        raw_ceo_input=ceo_input,
    )
