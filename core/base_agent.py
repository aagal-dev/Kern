"""Base agent contract and provider-neutral model state preparation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from core.model import ModelClient, ModelResponse
from integrations.ollama_client import OllamaClient


class BaseAgent:
    """Central reusable LLM-agent abstraction.

    Validates state, calls the configured model client, checks structured
    output, and returns a predictable result. Orchestration stays outside.
    """

    MAX_STATE_CHARS = 64_000

    def __init__(
        self,
        system_prompt: str | None,
        response_model: type[BaseModel],
        client: ModelClient | None = None,
    ) -> None:
        if not isinstance(system_prompt, (str, type(None))):
            raise TypeError("system_prompt must be a string or None.")

        if not isinstance(response_model, type) or not issubclass(
            response_model, BaseModel
        ):
            raise TypeError(
                "response_model must be a Pydantic BaseModel class."
            )

        self.client = client or OllamaClient()
        self.system_prompt = system_prompt or ""
        self.response_model = response_model

    def invoke(self, state: dict[str, Any]) -> BaseModel:
        if not isinstance(state, dict):
            return self._error("Agent state must be a dictionary.")

        try:
            if len(str(state)) > self.MAX_STATE_CHARS:
                return self._error("Agent state is too large.")
        except Exception:
            return self._error("Agent state could not be serialized.")

        # Isolate the invocation from external state mutation.
        state = dict(state)

        try:
            response = self.client.generate(
                state=state,
                response_model=self.response_model,
                system_prompt=self.system_prompt,
            )
        except Exception as exc:
            return self._error(
                "LLM client failure: "
                f"{str(exc)[:2000] or type(exc).__name__}"
            )

        if response is None:
            return self._error("LLM client returned no response.")

        if not isinstance(response, ModelResponse):
            return self._error(
                "LLM client returned an unexpected response type."
            )

        if not response.success:
            return self._error(
                response.error or "LLM generation failed."
            )

        if response.data is None:
            return self._error(
                "LLM returned success but no structured data."
            )

        if not isinstance(response.data, self.response_model):
            return self._error(
                "LLM client returned an unexpected response data type."
            )

        return response.data

    def _error(self, message: str) -> BaseModel:
        """Build an error instance of the configured response model.

        Prefers an 'error' field when the model supports it. Falls back
        to model_construct so required fields do not block error reporting.
        """
        try:
            return self.response_model(error=message)
        except (ValidationError, TypeError, ValueError):
            try:
                return self.response_model.model_construct(error=message)
            except Exception as exc:
                raise RuntimeError(
                    f"Could not build error response of type "
                    f"{self.response_model.__name__}: {message}"
                ) from exc


# Backward-compatible alias used by existing examples.
Agent = BaseAgent
