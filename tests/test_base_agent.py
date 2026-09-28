from typing import Any

from pydantic import BaseModel

from core.base_agent import BaseAgent
from core.model import ModelResponse
from core.runtime_state import RuntimeState


class AgentOutput(BaseModel):
    answer: str


class FakeModel:
    def generate(
        self,
        *,
        state: dict[str, Any],
        response_model: type[AgentOutput],
        system_prompt: str | None = None,
    ) -> ModelResponse[AgentOutput]:
        return ModelResponse(
            success=True,
            data=AgentOutput(answer=state["current_user_input"]),
        )


def test_agent_uses_injected_model_and_runtime_state() -> None:
    state = RuntimeState(current_user_input="hello")
    agent = BaseAgent(model=FakeModel(), response_model=AgentOutput)

    result = agent.run(state)

    assert result.answer == "hello"
