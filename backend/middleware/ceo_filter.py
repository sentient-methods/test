"""CEO Filter — translates technical agent output into executive-friendly language.

The CEO doesn't need to know about webpack configs or TypeScript generics.
They need to know: what was done, what decisions were made, and what's next.
"""

from __future__ import annotations

import anthropic

from backend.config import settings

FILTER_PROMPTS = {
    "executive": """\
You are a Chief of Staff summarizing a team's work for your CEO.
The CEO is non-technical and cares about OUTCOMES, not implementation details.

Rules:
- 1-3 sentences maximum
- Focus on what was accomplished, not how
- If there are decisions the CEO should know about, mention them
- If something needs the CEO's input, flag it clearly
- Never use technical jargon (no "API", "component", "refactor", "deploy pipeline")
- Use confident, action-oriented language
- End with a clear status: done, in progress, or needs input

Example: "Landing page is ready with a signup form and three feature sections.
Used your brand colors throughout. Ready for your review."
""",
    "manager": """\
You are a Chief of Staff summarizing a team's work for a manager-level audience.
Include key technical decisions but keep it digestible.

Rules:
- One short paragraph
- Mention technologies chosen and why (briefly)
- Note any trade-offs or assumptions made
- Flag risks or open questions
""",
    "technical": """\
Pass through the technical output with minimal filtering.
Just clean up formatting and add a brief executive summary at the top.
""",
}


async def filter_for_ceo(
    raw_output: str, agent_title: str, detail_level: str = "executive"
) -> str:
    """Filter agent output for the CEO based on their preferred detail level."""
    if detail_level == "technical":
        # At technical level, pass through with minimal filtering
        return f"**{agent_title}**: {raw_output}"

    prompt_template = FILTER_PROMPTS.get(detail_level, FILTER_PROMPTS["executive"])

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.model_ceo_filter,
        max_tokens=500,
        system=prompt_template,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The {agent_title} team just completed their work. "
                    f"Here's their raw output:\n\n{raw_output}\n\n"
                    "Summarize this for the CEO."
                ),
            }
        ],
    )

    return response.content[0].text
