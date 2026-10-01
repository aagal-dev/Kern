"""Demo script using the real Ollama client, MCP client, and the DateTool.
The script attempts to create a live LLM agent backed by Ollama. If Ollama is not
available, it falls back to the dummy model used previously. An MCP client is
instantiated (with no servers) to show how the SDK is imported – this does not
require a running server for the demo.
"""

from core.base_agent import Agent
from core.model import ModelResponse
from core.runtime_state import RuntimeState
from workflows.agent_with_tool import AgentWithLoop, AgentDecision
from kern.tools.datetime import DateTool

# Try to use the real Ollama client; fall back to a dummy implementation if the
# package is missing or the service is unreachable.
try:
    from kern.integrations.ollama_client import OllamaClient
except Exception:  # pragma: no cover – Ollama not installed in CI
    OllamaClient = None

# Minimal dummy model used as a fallback when Ollama is unavailable.
class DummyModel:
    def generate(self, state: dict, response_model=None, system_prompt=None):  # type: ignore[override]
        # Simple echo response.
        decision = AgentDecision(decision="response", response="Fallback dummy response.")
        return ModelResponse(success=True, data=decision)

# Attempt to create a real Ollama client; otherwise use the dummy.
client = OllamaClient() if OllamaClient is not None else DummyModel()

# Create the agent.
agent = Agent(system_prompt="You are a helpful assistant.", response_model=AgentDecision, client=client)

# Runtime state to track the conversation.
runtime = RuntimeState()

# Register the DateTool – this tool will be invoked by the LLM if appropriate.
tools = [DateTool()]

# Assemble the workflow.
workflow = AgentWithLoop(agent=agent, tools=tools, runtime_state=runtime)

# Demonstrate a user turn that asks for the current date.
user_input = "What is the current date?"
try:
    result = workflow.run(user_input)
    print("Agent response:", result)
except RuntimeError as exc:
    print("Agent raised an error (likely Ollama not available):", exc)

# Show MCP client import – this does not require a running server for the demo.
try:
    from kern.SDK.MCP.client.client import MCPClient
    # No servers configured; just instantiate to prove the import works.
    mcp_client = MCPClient([])
    print("MCP client instantiated successfully (no servers configured).")
except Exception as exc:
    print("Failed to instantiate MCP client:", exc)
