"""Ollama adapter implementing the model contract."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from core.model import ModelResponse

T = TypeVar("T", bound=BaseModel)


class OllamaClient:
    """Thin adapter over the Ollama chat API."""

    def __init__(
        self,
        model: str = "gpt-oss:120b-cloud",
        max_token_output: int = 4096,
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.max_token_output = max_token_output
        self.temperature = temperature

    def generate(
        self,
        state: dict[str, Any],
        response_model: type[T] | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse[T]:
        try:
            import ollama
        except ImportError as exc:
            return ModelResponse(
                success=False,
                error=f"ollama package is not installed: {exc}",
            )

        try:
            output_format = None
            if response_model is not None:
                output_format = response_model.model_json_schema()

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or "",
                    },
                    {
                        "role": "user",
                        "content": str(state),
                    },
                ],
                format=output_format,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_token_output,
                },
            )

            # Prefer attribute access; fall back to mapping for older shapes.
            message = getattr(response, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
            else:
                content = response["message"]["content"]

            if content is None:
                return ModelResponse(
                    success=False,
                    error="LLM returned an empty message content.",
                )

            if response_model is not None:
                try:
                    data = response_model.model_validate_json(content)
                except ValidationError as exc:
                    return ModelResponse(
                        success=False,
                        output=content,
                        error=(
                            "Output validation failed. "
                            f"Raw model output: {content[:1500]!r}. "
                            f"Details: {exc}"
                        ),
                    )
                return ModelResponse(
                    success=True,
                    output=content,
                    data=data,
                )

            return ModelResponse(
                success=True,
                output=content,
            )

        except ValidationError as exc:
            return ModelResponse(
                success=False,
                error=f"Output validation failed: {exc}",
            )
        except Exception as exc:
            return ModelResponse(
                success=False,
                error=str(exc)[:2000] or type(exc).__name__,
            )
