from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ToolInputT = TypeVar("ToolInputT", bound=BaseModel)


class ToolResult(BaseModel):
    """Standard result returned by a Kern tool."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Tool(ABC, Generic[ToolInputT]):
    """Technology-agnostic contract for an executable capability."""

    name: str
    description: str
    input_model: type[ToolInputT]

    @abstractmethod
    def execute(self, input: ToolInputT) -> ToolResult:
        """Execute the tool with validated structured input."""
        raise NotImplementedError

    @classmethod
    def definition(cls) -> dict[str, Any]:
        """Return a provider-neutral description of the tool."""
        return {
            "name": cls.name,
            "description": cls.description,
            "input_schema": cls.input_model.model_json_schema(),
        }
