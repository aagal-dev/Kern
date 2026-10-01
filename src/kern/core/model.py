"""Minimal model-client contract and normalized model response."""

from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelResponse(BaseModel, Generic[T]):
    """Normalized result from any model client."""

    success: bool
    data: T | None = None
    output: str | None = None
    error: str | None = None


class ModelClient(Protocol):
    """Provider-neutral contract for calling a language model."""

    def generate(
        self,
        state: dict[str, Any],
        response_model: type[T] | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse[T]:
        """Generate a response, optionally structured as response_model."""
        ...
