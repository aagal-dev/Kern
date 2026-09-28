# Kern

Reusable Python infrastructure for building agentic systems.

Initial foundation:

- `core/base_agent.py` — base agent contract and provider-neutral model state preparation.
- `core/tool.py` — technology-agnostic tool contract and standardized tool result.
- `core/runtime_state.py` — session runtime state: current input, conversation, and steps.
- `core/model.py` — minimal model-client contract and normalized model response.
- `integrations/ollama_client.py` — Ollama adapter implementing the model contract.

`runtime/`, `memory/`, and `workflows/` are reserved for later subsystems.
