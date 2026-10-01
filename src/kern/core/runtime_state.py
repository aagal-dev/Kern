from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class StepStatus(str, Enum):
    """Lifecycle status for a runtime step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConversationMessage(BaseModel):
    """A single message in the current session conversation."""

    model_config = ConfigDict(extra="forbid")

    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeStep(BaseModel):
    """A planned or executed step stored in session runtime state."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    step: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None


class RuntimeState(BaseModel):
    """Mutable state for one active agent session.

    This model intentionally represents session/execution context only.
    Persistent memory belongs to the separate memory subsystem.
    """

    model_config = ConfigDict(extra="forbid")

    current_user_input: str = ""
    conversation: list[ConversationMessage] = Field(default_factory=list)
    steps: list[RuntimeStep] = Field(default_factory=list)

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """Append a message to the current session conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.conversation.append(message)
        return message

    def add_step(
        self,
        step: str,
        *,
        status: StepStatus = StepStatus.PENDING,
        result: Any = None,
    ) -> RuntimeStep:
        """Create and append a runtime step."""
        runtime_step = RuntimeStep(step=step, status=status, result=result)
        self.steps.append(runtime_step)
        return runtime_step
