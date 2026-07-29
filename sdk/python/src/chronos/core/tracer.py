import json
import logging
import uuid
import cloudpickle
from datetime import datetime
from typing import Any, Dict, Optional, List
from contextlib import contextmanager

from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent
from chronos.core.determinism import deterministic_context

logger = logging.getLogger("chronos.sdk")

class Chronos:
    """Core SDK entrypoint for Chronos. Manages trace/step lifecycles and state checkpointing."""

    def __init__(self, agent_name: str = "default_agent", framework: str = "auto"):
        self.agent_name = agent_name
        self.current_trace: Optional[AgentTrace] = None
        self.active_spans: List[AgentSpan] = []
        self.events: List[Any] = []  # Holds steps/spans and checkpoints for the current trace
        
        # Framework initialization
        if framework == "auto":
            framework = _detect_framework()
            
        if framework not in _FRAMEWORK_LOADERS:
            raise ValueError(
                f"Unknown framework '{framework}'. "
                f"Choose from: {', '.join(sorted(_FRAMEWORK_LOADERS.keys()))}, auto"
            )
            
        loader_name = _FRAMEWORK_LOADERS[framework]
        loader_fn = globals()[loader_name]
        self.adapter = loader_fn(self)
        self.callback = self.adapter

    def start_trace(self, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AgentTrace:
        """Starts a new agent execution trace."""
        trace_id = uuid.uuid4()
        self.current_trace = AgentTrace(
            trace_id=trace_id,
            name=name or self.agent_name,
            status="running",
            metadata=metadata or {}
        )
        self.active_spans = []
        self.events = []
        logger.info(f"[Chronos] Started trace {trace_id} ({self.current_trace.name})")
        return self.current_trace

    def end_trace(self, status: str = "success") -> Optional[AgentTrace]:
        """Ends the current execution trace."""
        if not self.current_trace:
            logger.warning("[Chronos] Attempted to end trace, but no active trace exists.")
            return None

        self.current_trace.end_time = datetime.utcnow()
        self.current_trace.status = status
        logger.info(f"[Chronos] Ended trace {self.current_trace.trace_id} with status '{status}'")
        
        finished_trace = self.current_trace
        self.current_trace = None
        return finished_trace

    @contextmanager
    def trace(self, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, _force_trace_id: Optional[uuid.UUID] = None):
        """Context manager to start and automatically end an agent trace."""
        trace_obj = self.start_trace(name=name, metadata=metadata)
        if _force_trace_id:
            trace_obj.trace_id = _force_trace_id
            
        try:
            # Wrap the entire execution in the deterministic context using the trace_id as the seed
            with deterministic_context(str(trace_obj.trace_id)):
                yield trace_obj
            self.end_trace(status="success")
        except Exception as e:
            self.end_trace(status="error")
            raise e

    @contextmanager
    def step(self, name: str, step_type: str = "general", inputs: Optional[Dict[str, Any]] = None):
        """Context manager to record an execution step (LLM call, tool execution, reasoning)."""
        if not self.current_trace:
            self.start_trace()

        span_id = uuid.uuid4()
        parent_id = self.active_spans[-1].span_id if self.active_spans else None

        span_obj = AgentSpan(
            id=uuid.uuid4(),
            trace_id=self.current_trace.trace_id,
            span_id=span_id,
            parent_span_id=parent_id,
            name=name,
            span_type=step_type,
            status="running",
            inputs=inputs or {},
            timestamp=datetime.utcnow()
        )

        self.active_spans.append(span_obj)
        start_time = datetime.utcnow()
        try:
            yield span_obj
            span_obj.status = "success"
        except Exception as e:
            span_obj.status = "error"
            span_obj.outputs = {"error": str(e)}
            raise e
        finally:
            end_time = datetime.utcnow()
            span_obj.end_timestamp = end_time
            span_obj.duration_ms = (end_time - start_time).total_seconds() * 1000.0
            self.active_spans.pop()
            self.events.append(span_obj)

    # Alias step as span for OpenTelemetry compatibility
    span = step

    def checkpoint(self, state: Any, name: str = "state_checkpoint") -> CheckpointEvent:
        """Captures a snapshot of the current state using the Hybrid Serialization Strategy.
        
        Attempts JSON serialization first. If state contains non-JSON-serializable objects,
        it logs a warning and falls back to binary cloudpickle serialization.
        """
        if not self.current_trace:
            raise RuntimeError("[Chronos] Cannot capture checkpoint outside of an active trace.")

        current_span_id = self.active_spans[-1].span_id if self.active_spans else uuid.uuid4()
        
        is_binary = False
        serialized_state = None

        try:
            # Try standard JSON serialization
            serialized_state = json.dumps(state)
        except (TypeError, ValueError):
            # Fall back to cloudpickle magic
            logger.warning(
                f"[Chronos] State for checkpoint '{name}' is not JSON-serializable. "
                f"Falling back to cloudpickle binary serialization."
            )
            serialized_state = cloudpickle.dumps(state).hex()  # hex encoded binary string
            is_binary = True

        checkpoint_event = CheckpointEvent(
            id=uuid.uuid4(),
            trace_id=self.current_trace.trace_id,
            span_id=current_span_id,
            name=name,
            state_blob=serialized_state,
            is_binary=is_binary,
            timestamp=datetime.utcnow()
        )

        self.events.append(checkpoint_event)
        logger.info(f"[Chronos] State checkpoint captured (binary={is_binary})")
        return checkpoint_event

    # Alias snapshot as checkpoint for user preference
    snapshot = checkpoint


# ── Adapter factory ──────────────────────────────────────────────────

_FRAMEWORK_LOADERS = {
    "langchain": "_load_langchain",
    "langgraph": "_load_langgraph",
    "crewai": "_load_crewai",
    "google_adk": "_load_google_adk",
    "strands": "_load_strands",
    "raw": "_load_raw",
}


def _load_langchain(tracer: Chronos) -> Any:
    from chronos.adapters.langchain import ChronosLangchainCallback
    return ChronosLangchainCallback(tracer)


def _load_langgraph(tracer: Chronos) -> Any:
    from chronos.adapters.langgraph import ChronosCheckpointer
    return ChronosCheckpointer(tracer)


def _load_crewai(tracer: Chronos) -> Any:
    from chronos.adapters.crewai import ChronosCrewAIAdapter
    return ChronosCrewAIAdapter(tracer)


def _load_google_adk(tracer: Chronos) -> Any:
    from chronos.adapters.google_adk import ChronosADKAdapter
    return ChronosADKAdapter(tracer)


def _load_strands(tracer: Chronos) -> Any:
    from chronos.adapters.strands import ChronosStrandsAdapter
    return ChronosStrandsAdapter(tracer)


def _load_raw(tracer: Chronos) -> Any:
    from chronos.adapters.raw_python import ChronosRawAdapter
    return ChronosRawAdapter(tracer)


def _detect_framework() -> str:
    """Auto-detect which agent framework is installed."""
    detection_order = [
        ("google.adk", "google_adk"),
        ("langgraph", "langgraph"),
        ("langchain", "langchain"),
        ("crewai", "crewai"),
        ("strands", "strands"),
    ]
    for module_name, framework_key in detection_order:
        try:
            __import__(module_name)
            return framework_key
        except ImportError:
            continue
    return "raw"

