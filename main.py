from core.base_agent import Agent
from core.runtime_state import RuntimeState
from workflows.agent_with_tool import AgentDecision, AgentWithLoop
from tools.datetime import DateTool


agent = Agent(
    system_prompt="""
You are a helpful assistant.

You can either:
- respond directly to the user, or
- call one of the available tools.

Use a tool when it is necessary.
After receiving a tool result, decide whether to answer
the user or call another tool.
""",
    response_model=AgentDecision,
)

workflow = AgentWithLoop(
    agent=agent,
    tools=[DateTool()],
    runtime_state=RuntimeState(),
)

response = workflow.run(
    "What is today's date?"
)

print(response)