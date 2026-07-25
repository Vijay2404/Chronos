# Implementation Roadmap

- `[x]` **Phase 1: Core Data Models & Schemas**
  - `[x]` Define OpenTelemetry extension schemas (AgentTrace, AgentSpan, CheckpointEvent).
  - `[x]` Create protobuf/JSON schema definitions.

- `[x]` **Phase 2: Python SDK Foundation**
  - `[x]` Setup Core Tracer and OTEL exporter.
  - `[x]` Implement Determinism Module (random/datetime overriding).
  - `[x]` Implement VCR Interceptor Layer (requests/httpx mocking & recording).
  - `[x]` Implement Hybrid State Checkpointer (JSON primary, Cloudpickle fallback).

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
