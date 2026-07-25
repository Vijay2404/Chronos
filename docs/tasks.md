# Implementation Roadmap

- `[ ]` **Phase 1: Core Data Models & Schemas**
  - `[ ]` Define OpenTelemetry extension schemas (AgentTrace, AgentSpan, CheckpointEvent).
  - `[ ]` Create protobuf/JSON schema definitions.

- `[ ]` **Phase 2: Python SDK Foundation**
  - `[ ]` Setup Core Tracer and OTEL exporter.
  - `[ ]` Implement Determinism Module (random/datetime overriding).
  - `[ ]` Implement Network/LLM Interceptor hooks.
  - `[ ]` Implement Hybrid State Checkpointer (JSON primary, Cloudpickle fallback).

- `[ ]` **Phase 3: Framework Adapters**
  - `[ ]` Build LangChain callback handler adapter.
  - `[ ]` Build OpenAI native SDK wrapper.

- `[ ]` **Phase 4: Local Control Plane (MVP)**
  - `[ ]` Set up local FastAPI backend server.
  - `[ ]` Implement local DuckDB storage for traces.
  - `[ ]` Implement local filesystem storage for blob checkpoints.

- `[ ]` **Phase 5: Replay Engine (Remote Debugger)**
  - `[ ]` Build Replay runner context manager in SDK.
  - `[ ]` Implement fetching mocked state from local backend.
  - `[ ]` Add branching logic (switching to live execution).

- `[ ]` **Phase 6: DevTools UI**
  - `[ ]` Initialize Next.js project.
  - `[ ]` Build Trace Timeline (Flame Graph) component.
  - `[ ]` Build State Inspector component.
