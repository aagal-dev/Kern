# Kern

Reusable Python infrastructure for building agentic systems.

## Foundation

- `core/base_agent.py` — base agent contract (`BaseAgent` / `Agent`) and provider-neutral model calls
- `core/model.py` — minimal model-client contract and normalized `ModelResponse`
- `core/tool.py` — technology-agnostic tool contract and standardized `ToolResult`
- `core/runtime_state.py` — session runtime state: current input, conversation, and steps
- `integrations/ollama_client.py` — Ollama adapter implementing the model contract
- `workflows/agent_with_tool.py` — ready-made agent + tool loop with structured `AgentDecision`
- `tools/datetime.py` — example date tool

`runtime/` and `memory/` are reserved for later subsystems.

## Quick start

```bash
pip install pydantic ollama
# Start Ollama and pull a model that supports structured output, then:
python main.py
```

Without a running Ollama server the example raises a clear connection error.

Unit and runtime tests use a fake model client and do not need Ollama:

```bash
python -m pytest tests/ -v
```

## Design notes

- Contracts live in `core/`. Provider-specific code stays in `integrations/`.
- Structured agent decisions are validated with Pydantic. Invalid model output is turned into a clear error instead of a silent failure.
- The system prompt in `main.py` describes the exact JSON shape the model must return so validation errors are less common.
