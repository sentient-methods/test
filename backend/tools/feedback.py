"""Feedback tools — mechanisms for agents to surface decisions back to the CEO.

When an agent encounters ambiguity or needs a decision, these tools
capture the question and present it through the CEO-friendly interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FeedbackPriority(str, Enum):
    LOW = "low"          # Nice to know, won't block
    MEDIUM = "medium"    # Should know, might affect outcome
    HIGH = "high"        # Blocks progress, needs CEO input
    CRITICAL = "critical"  # Can't proceed without answer


@dataclass
class FeedbackItem:
    """A question or decision point surfaced by an agent."""
    id: str
    agent: str
    question: str
    options: list[str] = field(default_factory=list)
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    context: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    answer: str | None = None


@dataclass
class FeedbackQueue:
    """Queue of pending feedback items from agents."""
    _items: list[FeedbackItem] = field(default_factory=list)
    _counter: int = 0

    def add(
        self,
        agent: str,
        question: str,
        options: list[str] | None = None,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        context: str = "",
    ) -> FeedbackItem:
        self._counter += 1
        item = FeedbackItem(
            id=f"fb-{self._counter}",
            agent=agent,
            question=question,
            options=options or [],
            priority=priority,
            context=context,
        )
        self._items.append(item)
        return item

    def resolve(self, item_id: str, answer: str) -> FeedbackItem | None:
        for item in self._items:
            if item.id == item_id:
                item.resolved = True
                item.answer = answer
                return item
        return None

    def pending(self) -> list[FeedbackItem]:
        return [i for i in self._items if not i.resolved]

    def format_for_ceo(self) -> str:
        """Format pending items as CEO-friendly questions."""
        pending = self.pending()
        if not pending:
            return ""

        lines = ["I have a few questions before we proceed:\n"]
        for i, item in enumerate(pending, 1):
            lines.append(f"{i}. {item.question}")
            if item.options:
                for opt in item.options:
                    lines.append(f"   - {opt}")
            if item.context:
                lines.append(f"   (Context: {item.context})")
            lines.append("")

        return "\n".join(lines)


# Global feedback queue
feedback_queue = FeedbackQueue()
