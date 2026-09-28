from typing import Any

from pydantic import BaseModel

from core.base_agent import BaseAgent
from core.model import ModelResponse
from core.runtime_state import RuntimeState


class AgentOutput(BaseModel):
    answer: str
    error: str | None = None


class FakeModel:
    def generate(
        self,
        state: dict[str, Any],
        response_model: type[AgentOutput] | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse[AgentOutput]:
        return ModelResponse(
            success=True,
            data=AgentOutput(answer=state.get("current_user_input", "")),
        )


class FailingModel:
    def generate(
        self,
        state: dict[str, Any],
        response_model: type[AgentOutput] | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse[AgentOutput]:
        return ModelResponse(
            success=False,
            error="simulated provider failure",
        )


def test_agent_uses_injected_model_and_runtime_state() -> None:
    state = RuntimeState(current_user_input="hello")
    agent = BaseAgent(
        system_prompt="test",
        response_model=AgentOutput,
        client=FakeModel(),
    )

    result = agent.invoke(state.model_dump(mode="json"))

    assert isinstance(result, AgentOutput)
    assert result.answer == "hello"
    assert result.error is None


def test_agent_turns_provider_failure_into_error_response() -> None:
    agent = BaseAgent(
        system_prompt="test",
        response_model=AgentOutput,
        client=FailingModel(),
    )

    result = agent.invoke({"current_user_input": "hi"})

    assert isinstance(result, AgentOutput)
    assert result.error == "simulated provider failure"
