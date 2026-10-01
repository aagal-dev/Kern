import importlib, sys

# Re-export submodules so ``import core.base_agent`` works.
for _mod in [
    "base_agent",
    "model",
    "runtime_state",
    "tool",
]:
    full_name = f"kern.core.{_mod}"
    sys.modules[f"core.{_mod}"] = importlib.import_module(full_name)

# Export top‑level symbols for convenience.
from kern.core.base_agent import Agent, BaseAgent  # noqa: F401
from kern.core.model import ModelClient, ModelResponse  # noqa: F401
from kern.core.runtime_state import (
    ConversationMessage,
    RuntimeState,
    RuntimeStep,
    StepStatus,
)  # noqa: F401
from kern.core.tool import Tool, ToolResult  # noqa: F401

