"""Ready-made agent + tool loop workflow."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from kern.core.base_agent import Agent
from kern.core.runtime_state import RuntimeState, StepStatus
from kern.core.tool import Tool, ToolResult


class ToolCall(BaseModel):
    """A single tool invocation requested by the agent."""

    name: str = Field(description="Exact name of the tool to call.")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments matching the tool's input schema.",
    )


class AgentDecision(BaseModel):
    """Structured decision the agent must return on every turn.

    Exactly one of these shapes is valid:
    - decision='response' + non-empty response text, tool_call=null, error=null
    - decision='tool_call' + tool_call object, response=null, error=null
    - error set (framework use only) — other fields ignored
    """

    decision: Literal["response", "tool_call"] | None = Field(
        default=None,
        description="Must be 'response' or 'tool_call' when error is null.",
    )
    response: str | None = Field(
        default=None,
        description="User-facing answer when decision is 'response'.",
    )
    tool_call: ToolCall | None = Field(
        default=None,
        description="Tool to invoke when decision is 'tool_call'.",
    )
    error: str | None = Field(
        default=None,
        description="Framework error message; leave null for normal turns.",
    )

    @model_validator(mode="after")
    def validate_decision(self) -> "AgentDecision":
        if self.error is not None:
            return self

        if self.decision == "response":
            if not self.response or not str(self.response).strip():
                raise ValueError(
                    "response decision requires a non-empty response."
                )
            if self.tool_call is not None:
                raise ValueError(
                    "response decision must not contain a tool call."
                )
            return self

        if self.decision == "tool_call":
            if self.tool_call is None:
                raise ValueError(
                    "tool_call decision requires a tool call."
                )
            if self.response is not None:
                raise ValueError(
                    "tool_call decision must not contain a response."
                )
            return self

        raise ValueError(
            "decision must be either 'response' or 'tool_call'."
        )


class AgentWithLoop:
    """Run an agent repeatedly until it returns a user-facing response."""

    def __init__(
        self,
        agent: Agent,
        tools: list[Tool[Any]],
        runtime_state: RuntimeState,
        max_iterations: int = 8,
    ) -> None:
        if max_iterations <= 0:
            raise ValueError("max_iterations must be greater than zero.")

        if agent.response_model is not AgentDecision:
            raise TypeError(
                "AgentWithLoop requires the agent's response_model "
                "to be AgentDecision."
            )

        self.agent = agent
        self.tools = {tool.name: tool for tool in tools}
        self.runtime_state = runtime_state
        self.max_iterations = max_iterations

    def run(self, user_input: str) -> str:
        """Run one user turn through the agent/tool loop."""
        if not isinstance(user_input, str):
            raise TypeError("user_input must be a string.")

        user_input = user_input.strip()

        if not user_input:
            raise ValueError("user_input must not be empty.")

        self.runtime_state.current_user_input = user_input
        self.runtime_state.add_message("user", user_input)

        for _ in range(self.max_iterations):
            state = self.runtime_state.model_dump(mode="json")
            state["available_tools"] = [
                tool.definition() for tool in self.tools.values()
            ]

            decision = self.agent.invoke(state)

            if not isinstance(decision, AgentDecision):
                raise TypeError(
                    "Agent returned an unexpected decision type."
                )

            if decision.error:
                raise RuntimeError(decision.error)

            if decision.decision == "response":
                response = decision.response

                if response is None:
                    raise RuntimeError(
                        "Agent returned a response decision without a response."
                    )

                self.runtime_state.add_message("assistant", response)
                return response

            tool_call = decision.tool_call

            if tool_call is None:
                raise RuntimeError(
                    "Agent returned a tool_call decision without a tool call."
                )

            tool = self.tools.get(tool_call.name)

            if tool is None:
                tool_result = ToolResult(
                    success=False,
                    error=f"Unknown tool: {tool_call.name!r}.",
                )
            else:
                try:
                    arguments = tool.input_model.model_validate(
                        tool_call.arguments
                    )
                except ValidationError as exc:
                    tool_result = ToolResult(
                        success=False,
                        error=f"Invalid tool arguments: {exc}",
                    )
                else:
                    tool_result = tool.execute(arguments)

            self.runtime_state.add_step(
                step=f"tool:{tool_call.name}",
                status=(
                    StepStatus.COMPLETED
                    if tool_result.success
                    else StepStatus.FAILED
                ),
                result=tool_result.model_dump(mode="json"),
            )

            self.runtime_state.add_message(
                "tool",
                tool_result.model_dump_json(),
                metadata={"tool_name": tool_call.name},
            )

        raise RuntimeError(
            f"Agent loop exceeded max_iterations={self.max_iterations}."
        )
