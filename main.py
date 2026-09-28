from core.base_agent import Agent
from core.runtime_state import RuntimeState
from workflows.agent_with_tool import AgentDecision, AgentWithLoop
from tools.datetime import DateTool


SYSTEM_PROMPT = """
You are a helpful assistant.

On every turn you must return a single JSON object with exactly these fields:
- decision: either "response" or "tool_call"
- response: a non-empty string when decision is "response", otherwise null
- tool_call: an object {"name": "...", "arguments": {...}} when decision is "tool_call", otherwise null
- error: always null (the framework sets this)

Rules:
1. If you can answer the user directly, set decision="response" and put the answer in response.
2. If you need a tool, set decision="tool_call", fill tool_call with the exact tool name and arguments, and leave response null.
3. Never set both response and tool_call at the same time.
4. Never invent tool names. Only use tools listed in available_tools.
5. After a tool result appears in the conversation, decide again: answer the user or call another tool.

Use a tool only when it is necessary to answer correctly.
""".strip()


agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    response_model=AgentDecision,
)

workflow = AgentWithLoop(
    agent=agent,
    tools=[DateTool()],
    runtime_state=RuntimeState(),
)

if __name__ == "__main__":
    response = workflow.run("What is today's date?")
    print(response)
