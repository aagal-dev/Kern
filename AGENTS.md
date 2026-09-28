# AGENTS.md — Kern

> Canonical context for coding agents working on **Kern**, our reusable Python infrastructure/SDK for agentic systems. Read this before changing framework code.

## Contents

**Mission · Architecture · Core components · Runtime · Structure · Engineering rules · Context engineering · Reliability/security · Testing · Coding-agent rules · Component map**

---

## 1. Mission

**Kern = reusable execution infrastructure for agentic systems.**

It exists so new projects do not repeatedly rebuild agents, runtime control, state handling, tools, memory, model adapters, embeddings, storage, and observability.

```text
Kern owns:      reusable infrastructure + contracts + execution semantics
Application owns: product logic + domain behavior + policies + workflows
```

### Design goals

- Small, readable public interfaces.
- Components are reusable, composable, and swappable.
- Runtime state is explicit and inspectable.
- External dependencies stay at integration boundaries.
- Execution is bounded, testable, and observable.
- LLM context/tool schemas are designed for machine + human readability.
- Prefer the smallest abstraction that solves a real problem.

Kern is **not** a product, chatbot, domain workflow, or mandatory multi-agent architecture.

---

## 2. Architecture

```text
APPLICATION
  │  agents / workflows / policies / APIs
  ▼
RUNTIME
  │  orchestration / planning / execution / lifecycle
  ▼
AGENT CORE
  │  BaseAgent / state / invocation / validation / context
  ▼
CONTRACTS
  │  model / tools / memory / embeddings / storage / planner
  ▼
INTEGRATIONS
     Ollama / Cohere / Qdrant / HTTP APIs / external tools
```

**Dependency direction:** `application → Kern → contracts → integrations`

### Non-negotiable architecture rules

1. **Contracts before replaceable implementations.**
2. **One responsibility per component.**
3. **Explicit over magical:** no hidden global state or invisible persistence.
4. **Stable core, flexible edges:** provider-specific code belongs in integrations.
5. **Application logic stays out of Kern.**
6. **Deterministic control where possible; bounded autonomy where necessary.**

---

## 3. Core components

### `BaseAgent`

Central reusable LLM-agent abstraction.

```python
result = agent.invoke(
    user_input=input_text,
    state=state,
    available_tools=tools,
)
```

Responsibilities: validate inputs, assemble context, call the configured model provider, expose tools, validate structured output, enforce bounds, normalize errors, return a predictable result.

Do **not** put orchestration, product logic, vendor-specific persistence, or application policy inside `BaseAgent`.

### Working memory = explicit runtime state

Working memory is the **current session/execution state**, not a second hidden memory system.

```text
state = {
  user_input,
  conversation,
  objective,
  steps,
  current_step_id,
  tool_context,
  runtime_metadata,
}
```

Distinguish:

```text
working state   → current execution
conversation    → persisted chat/history
episodic memory → meaningful prior events
retrieval       → embeddings/search over stored information
```

Keep state bounded and inspectable. Do not create another working-memory abstraction without a distinct reason.

### Model provider

```text
ModelProvider → invoke/generate → model response
```

Provider implementations may use Ollama or remote HTTP APIs. Generic core APIs must not depend on vendor-specific request/response objects.

### Context / prompt assembly

```text
input + state + relevant memory + tool schemas
                    ↓
             context assembly
                    ↓
               model request
```

Context should be **minimal sufficient context**, not maximum context. Keep stable instructions separate from dynamic/untrusted data; bound the context; avoid duplication; never fabricate missing information.

### Tools

```text
Agent → tool schema → validate/authorize → execute → result → state/context
```

Tools are explicit capabilities, not arbitrary model-controlled access. Validate arguments, enforce permissions and limits, normalize errors, and sanitize sensitive outputs.

### Planner

Planning is optional. Support:

```text
simple request  → direct execution
complex request → objective → explicit steps → runtime execution
```

Plans contain **objectives, steps, status, dependencies/results** as data. Do not design Kern around storing hidden chain-of-thought.

### Runtime / orchestrator

Owns execution control, not domain intelligence.

- create/load state
- direct vs planned path
- execute agents/tools/steps
- update state
- timeout/cancel/limit execution
- emit events/traces
- terminate cleanly

Never create an unconstrained autonomous loop.

### Memory / storage

Optional, separate responsibilities:

```text
conversation store   | history
episodic store       | meaningful events
vector store         | semantic retrieval
other persistence    | application-specific data
```

Episodic memory stores concise useful experiences + metadata, not blind copies of all conversation. Avoid invented temporal labels/facts.

### Embeddings

```text
EmbeddingProvider → vectors → VectorStore
```

Current direction: Cohere Embed v4 via `httpx`; keep that provider-specific detail inside the integration. Never leak Cohere-specific APIs into generic memory contracts.

### Higher-level agents

Reusable agents (for example, conversation agents) compose Kern primitives. Multi-agent composition is optional, not a framework requirement.

---

## 4. Runtime model

```text
INPUT
  ↓
load/create state
  ↓
direct OR plan
  ↓
assemble context
  ↓
invoke agent/model
  ↓
validate result
  ↓
execute approved tools
  ↓
update state
  ↓
repeat until explicit termination
  ↓
persist required memory/history
  ↓
normalized result
```

### Planned execution

```text
request → planner → objective/steps
                       ↓
                    runtime
                       ↓
              current step → agent/tool
                       ↓
                   result/state
                       └────→ next step
```

The runtime is the shared execution boundary. State transitions should be explicit and traceable.

---

## 5. Project structure

Logical target structure. **Do not create empty components just to match it. Existing compatible repository structure wins.**

```text
project/
├─ kern/
│  ├─ agent_core/
│  │  ├─ base_agent.py
│  │  ├─ result.py
│  │  └─ errors.py
│  ├─ runtime/
│  │  ├─ orchestrator.py
│  │  ├─ executor.py
│  │  └─ events.py
│  ├─ contracts/
│  │  ├─ model.py
│  │  ├─ tools.py
│  │  ├─ memory.py
│  │  ├─ embeddings.py
│  │  ├─ planner.py
│  │  └─ storage.py
│  ├─ context/
│  │  ├─ assembler.py
│  │  ├─ prompts.py
│  │  └─ schemas.py
│  ├─ planner/
│  │  ├─ planner.py
│  │  └─ models.py
│  ├─ tools/
│  │  ├─ base.py
│  │  └─ registry.py
│  └─ memory/
│     ├─ episodic/
│     ├─ conversation/
│     └─ retrieval/
├─ integrations/
│  ├─ ollama_client.py
│  ├─ cohere_client.py
│  ├─ qdrant_store.py
│  └─ ...
├─ agents/
├─ config/
└─ tests/
   ├─ unit/
   ├─ contract/
   ├─ integration/
   └─ runtime/
```

---

## 6. Engineering rules

### Interfaces

- Keep public contracts small, stable, and obvious.
- Prefer composition over deep inheritance.
- Depend on contracts, not concrete vendors.
- Keep integrations at the edge.
- Avoid circular dependencies and speculative dependency-injection frameworks.
- Do not leak vendor types through generic public APIs.

### State

- Explicit, bounded, serializable where practical.
- Important state should use typed schemas.
- Do not silently mutate unrelated application state.
- Preserve causality: know what operation changed what state.

### Errors

Handle and preserve cause for: validation errors, provider failures, timeouts/cancellation, tool failures, malformed model output, and persistence failures.

Never use broad exception swallowing such as `except Exception: pass`.

### Secrets / security

```text
authenticate → authorize → validate → limit → execute → sanitize
```

- Secrets never belong in source, prompts, logs, or persistent state.
- Treat model output, retrieved text, and tool output as untrusted data.
- Prompt injection cannot grant authority the runtime did not grant.
- Arbitrary shell/network/filesystem access must only exist behind explicit tools and policy.

---

## 7. Context + prompt engineering

Use a predictable context hierarchy:

```text
RULES / ROLE
    ↓
TASK / OBJECTIVE
    ↓
RELEVANT STATE
    ↓
RELEVANT MEMORY
    ↓
TOOLS + SCHEMAS
    ↓
CURRENT INPUT
```

Rules:

- Optimize for **context quality, not context quantity**.
- Provide the smallest sufficient context.
- Prefer structured fields for structured data.
- Separate instructions from untrusted retrieved/tool content.
- Do not ask the model to “remember” data already owned by runtime state.
- Avoid duplicating the same information in hidden state and prompt text without reason.
- Keep prompts versionable and testable.
- Never make critical security policy prompt-only.

Execution data should store **plans, steps, decisions, tool calls, and results**—not hidden chain-of-thought.

---

## 8. Reliability + observability

Default posture:

```text
validate → bound → execute → record → fail clearly
```

Bound model calls, tool calls, step/recursion count, execution time, retries, and context size.

Retries must be bounded and safe; do not blindly retry non-idempotent actions.

Useful trace shape:

```text
run_id → agent/step → model/tool call → latency → result → state transition
```

Prefer structured logs/events. Never log secrets or sensitive payloads.

---

## 9. Testing

```text
unit       → local behavior
contract   → provider/interface compatibility
integration→ real external boundaries
runtime    → multi-step execution + termination
```

At minimum test: state bounds, structured-output validation, tool validation/authorization, timeouts/cancellation, provider failure propagation, planner/runtime transitions, termination, and persistence/retrieval contracts.

A replacement implementation of a contract should pass the same contract tests whenever behavior is intended to remain equivalent.

---

## 10. Coding-agent rules

Follow:

```text
READ → SEARCH → UNDERSTAND → PATCH → TEST → REVIEW
```

Before coding:

1. Read this file and the relevant implementation.
2. Search for an existing abstraction before creating one.
3. Identify the smallest component/boundary that owns the change.

While coding:

- Reuse existing primitives.
- Keep changes local.
- Preserve contracts unless a breaking change is explicitly required.
- Keep provider-specific logic in integrations.
- Validate boundaries.
- Do not refactor unrelated code.
- Do not build speculative components for hypothetical future needs.

After coding:

- Run focused tests, then broader tests when useful.
- Check imports and dependency direction.
- Check error paths, bounds, security, and secret handling.
- Ensure the change did not duplicate an existing responsibility.

**The coding agent implements the architecture; it should not casually redesign Kern.**

---

## 11. Current component map

```text
KERN
├─ Agent Core      → BaseAgent / invocation / typed results
├─ Runtime         → orchestrator / executor / lifecycle
├─ Planner         → objective / explicit steps
├─ Context         → assembly / prompts / schemas / budgeting
├─ Tools           → schemas / registry / safe execution
├─ Memory          → working state / episodic / conversation / retrieval
├─ Storage         → persistence + vector contracts
├─ Model           → ModelProvider + implementations
├─ Embeddings      → EmbeddingProvider + implementations
├─ Integrations    → Ollama / Cohere HTTP / Qdrant / external APIs
├─ Observability   → logs / events / traces
└─ Tests            → unit / contract / integration / runtime
```

### Mental model

> **Kern is the reusable execution substrate for agentic systems.** `BaseAgent` handles invocation; `state` carries working context; `planner` describes work; `runtime` controls execution; contracts keep implementations swappable; integrations talk to external systems; applications define actual behavior.

When uncertain, choose the design that is **smaller, more explicit, easier to replace, easier to test, and easier for another coding agent to understand**.
