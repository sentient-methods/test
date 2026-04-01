"""Progressive disclosure — controls how much detail surfaces to the CEO.

The CEO sees executive summaries by default. They can drill down by asking
for more detail ("show me more", "what exactly did you do?", "technical details").
"""

from __future__ import annotations

# Keywords that signal the CEO wants more detail
DETAIL_ESCALATION_KEYWORDS = {
    "technical": [
        "show me the code",
        "technical details",
        "what exactly",
        "show me everything",
        "full details",
        "raw output",
        "debug",
        "verbose",
    ],
    "manager": [
        "tell me more",
        "more detail",
        "elaborate",
        "explain why",
        "what decisions",
        "trade-offs",
        "show me more",
    ],
}


def detect_detail_level(ceo_input: str) -> str | None:
    """Detect if the CEO is asking for a different level of detail.

    Returns the detected level, or None if no change is requested.
    """
    lower = ceo_input.lower()

    for level, keywords in DETAIL_ESCALATION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower:
                return level

    # Check for explicit de-escalation
    if any(phrase in lower for phrase in ["keep it simple", "summary", "just the highlights", "bottom line"]):
        return "executive"

    return None
