"""Runtime tests for the agent + tool loop with a fake model client."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from core.base_agent import Agent
from core.model import ModelResponse
from core.runtime_state import RuntimeState
from core.tool import Tool, ToolResult
from workflows.agent_with_tool import AgentDecision, AgentWithLoop, ToolCall


class EchoInput(BaseModel):
    text: str


class EchoTool(Tool[EchoInput]):
    name = "echo"
    description = "Return the provided text."
    input_model = EchoInput

    def execute(self, input: EchoInput) -> ToolResult:
        return ToolResult(success=True, output=input.text)


class ScriptedModel:
    """Returns a fixed sequence of AgentDecision values."""

    def __init__(self, decisions: list[AgentDecision | ModelResponse]) -> None:
        self._decisions = list(decisions)
        self.calls = 0

    def generate(
        self,
        state: dict[str, Any],
        response_model: type | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse[AgentDecision]:
        self.calls += 1
        if not self._decisions:
            return ModelResponse(
                success=False,
                error="No more scripted decisions.",
            )
        item = self._decisions.pop(0)
        if isinstance(item, ModelResponse):
            return item
        return ModelResponse(success=True, data=item)


def test_loop_returns_direct_response() -> None:
    model = ScriptedModel(
        [
            AgentDecision(
                decision="response",
                response="Hello there.",
            )
        ]
    )
    agent = Agent(
        system_prompt="test",
        response_model=AgentDecision,
        client=model,
    )
    workflow = AgentWithLoop(
        agent=agent,
        tools=[],
        runtime_state=RuntimeState(),
    )

    result = workflow.run("hi")

    assert result == "Hello there."
    assert model.calls == 1


def test_loop_calls_tool_then_responds() -> None:
    model = ScriptedModel(
        [
            AgentDecision(
                decision="tool_call",
                tool_call=ToolCall(name="echo", arguments={"text": "ping"}),
            ),
            AgentDecision(
                decision="response",
                response="Tool said: ping",
            ),
        ]
    )
    agent = Agent(
        system_prompt="test",
        response_model=AgentDecision,
        client=model,
    )
    state = RuntimeState()
    workflow = AgentWithLoop(
        agent=agent,
        tools=[EchoTool()],
        runtime_state=state,
    )

    result = workflow.run("use the echo tool")

    assert result == "Tool said: ping"
    assert model.calls == 2
    assert len(state.steps) == 1
    assert state.steps[0].step == "tool:echo"
    assert state.steps[0].result["success"] is True


def test_loop_surfaces_validation_error_from_model() -> None:
    """When the model client reports a validation failure, the loop raises it."""
    model = ScriptedModel(
        [
            ModelResponse(
                success=False,
                error=(
                    "Output validation failed. "
                    "Raw model output: '{}'. "
                    "Details: decision must be either 'response' or 'tool_call'."
                ),
            )
        ]
    )
    agent = Agent(
        system_prompt="test",
        response_model=AgentDecision,
        client=model,
    )
    workflow = AgentWithLoop(
        agent=agent,
        tools=[],
        runtime_state=RuntimeState(),
    )

    try:
        workflow.run("anything")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "Output validation failed" in str(exc)
        assert "decision must be either" in str(exc)


def test_agent_decision_rejects_empty_response() -> None:
    try:
        AgentDecision(decision="response", response="   ")
        assert False, "expected validation error"
    except Exception as exc:
        assert "non-empty response" in str(exc)


def test_agent_decision_accepts_error_only() -> None:
    d = AgentDecision(error="something went wrong")
    assert d.error == "something went wrong"
    assert d.decision is None
