"""Cost tracker — monitors API spend per session.

Tracks token usage and estimates cost across all agent calls.
The CEO should always know what things cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# Pricing per million tokens (as of model catalog)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_cost_per_M, output_cost_per_M)
    "claude-opus-4-6": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    # Aliases
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}


@dataclass
class UsageEntry:
    """A single API call's token usage."""
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionCost:
    """Tracks cumulative cost for a session."""
    session_id: str
    entries: list[UsageEntry] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(e.cost_usd for e in self.entries)

    @property
    def total_input_tokens(self) -> int:
        return sum(e.input_tokens for e in self.entries)

    @property
    def total_output_tokens(self) -> int:
        return sum(e.output_tokens for e in self.entries)

    def add(self, agent: str, model: str, input_tokens: int, output_tokens: int) -> UsageEntry:
        pricing = MODEL_PRICING.get(model, (5.00, 25.00))  # Default to Opus pricing
        cost = (input_tokens * pricing[0] / 1_000_000) + (output_tokens * pricing[1] / 1_000_000)
        entry = UsageEntry(
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        self.entries.append(entry)
        return entry

    def summary(self) -> dict:
        """CEO-friendly cost summary."""
        by_agent: dict[str, float] = {}
        for e in self.entries:
            by_agent[e.agent] = by_agent.get(e.agent, 0) + e.cost_usd

        return {
            "session_id": self.session_id,
            "total_cost_usd": round(self.total_cost, 4),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "call_count": len(self.entries),
            "cost_by_agent": {k: round(v, 4) for k, v in by_agent.items()},
        }

    def estimate_monthly_run_cost(self) -> dict:
        """Rough estimate of what it would cost to run this session's
        output as a live service (hosting, not AI costs)."""
        return {
            "note": "AI costs are per-interaction only. No ongoing AI cost for running the built app.",
            "railway_hobby": "$5/mo (includes this service)",
            "railway_pro": "$20/mo (for production workloads)",
        }


class CostTracker:
    """Global cost tracker across all sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionCost] = {}

    def get_or_create(self, session_id: str) -> SessionCost:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionCost(session_id=session_id)
        return self._sessions[session_id]

    def track(self, session_id: str, agent: str, model: str, input_tokens: int, output_tokens: int) -> UsageEntry:
        session_cost = self.get_or_create(session_id)
        return session_cost.add(agent, model, input_tokens, output_tokens)

    def get_summary(self, session_id: str) -> dict:
        session_cost = self.get_or_create(session_id)
        return session_cost.summary()

    def get_total_spend(self) -> dict:
        total = sum(sc.total_cost for sc in self._sessions.values())
        return {
            "total_cost_usd": round(total, 4),
            "session_count": len(self._sessions),
            "sessions": {sid: sc.summary() for sid, sc in self._sessions.items()},
        }


# Global tracker
cost_tracker = CostTracker()
