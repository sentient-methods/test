"""Message models for the chat protocol between frontend and backend."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    CEO = "ceo"  # The user — always the CEO
    SYSTEM = "system"  # MakeItHappen system messages
    AGENT = "agent"  # Agent activity updates


class AgentPhase(str, Enum):
    """Which functional area is currently active."""
    CHIEF_OF_STAFF = "chief_of_staff"
    PRODUCT_OWNER = "product_owner"
    DESIGNER = "designer"
    ENGINEER = "engineer"
    QA = "qa"
    DEVOPS = "devops"


class AgentStatus(str, Enum):
    THINKING = "thinking"
    WORKING = "working"
    COMPLETE = "complete"
    BLOCKED = "blocked"


# --- Inbound (CEO -> System) ---

class CEOMessage(BaseModel):
    """Message from the CEO (user)."""
    content: str
    session_id: str | None = None
    detail_level: str = "executive"  # executive | manager | technical


# --- Outbound (System -> CEO) ---

class SystemResponse(BaseModel):
    """A response chunk streamed back to the CEO."""
    type: str  # "message" | "agent_status" | "clarification" | "preview" | "done"
    content: str = ""
    agent: AgentPhase | None = None
    agent_status: AgentStatus | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClarificationRequest(BaseModel):
    """When the system needs the CEO's input before proceeding."""
    questions: list[str]
    context: str  # Why we're asking
    agent: AgentPhase
