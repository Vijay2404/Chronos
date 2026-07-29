import os
import atexit
import json
from pathlib import Path
from typing import Optional, Callable

from chronos.core.tracer import Chronos
from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent
from chronos.interceptors.vcr import VCREngine, VCRMode

_global_tracer: Optional[Chronos] = None
_vcr_engine: Optional[VCREngine] = None

def init(project: str = "default_agent") -> None:
    """
    Initialize the Chronos SDK globally.
    This applies the 'Horizontal Bar' of our T-Shaped DX:
    1. Instantiates the global tracer.
    2. Detects CHRONOS_REPLAY_MODE.
    3. Globally patches network IO via VCREngine.
    4. Overrides determinism (time, random) based on trace_id.
    """
    global _global_tracer, _vcr_engine
    
    if _global_tracer is not None:
        return  # Already initialized

    _global_tracer = Chronos(agent_name=project)
    
    replay_trace_id = os.environ.get("CHRONOS_REPLAY_MODE")
    
    if replay_trace_id:
        _vcr_engine = VCREngine(mode=VCRMode.REPLAY)
        # TODO (Phase 4): Fetch cassettes from DuckDB/FS using replay_trace_id
        # For now, we look for a local fallback file if it exists
        cassette_path = Path(".chronos_cassettes.json")
        if cassette_path.exists():
            from chronos.interceptors.vcr import VCRCassette
            with open(cassette_path, "r") as f:
                data = json.load(f)
                cassettes = [VCRCassette(**c) for c in data]
                _vcr_engine.load_cassettes(cassettes)
    else:
        _vcr_engine = VCREngine(mode=VCRMode.RECORD)
        
    _vcr_engine.start()

def _save_cassettes_on_exit():
    """Temporary helper to save cassettes to disk before Phase 4 storage is built."""
    if _vcr_engine and _vcr_engine.mode == VCRMode.RECORD and _vcr_engine.cassettes:
        try:
            with open(".chronos_cassettes.json", "w") as f:
                json.dump([c.model_dump() for c in _vcr_engine.cassettes], f, indent=2)
        except Exception:
            pass

atexit.register(_save_cassettes_on_exit)

def step(name: str = "step") -> Callable:
    """Global decorator to trace a function as an agent step."""
    if not _global_tracer:
        init()
    # Fallback to the raw adapter's step method if using raw python
    if hasattr(_global_tracer.adapter, "step"):
        return _global_tracer.adapter.step(name)
    def dummy_decorator(func): return func
    return dummy_decorator

def tool(name: str = "tool") -> Callable:
    """Global decorator to trace a function as a tool."""
    if not _global_tracer:
        init()
    if hasattr(_global_tracer.adapter, "tool"):
        return _global_tracer.adapter.tool(name)
    def dummy_decorator(func): return func
    return dummy_decorator

def get_tracer() -> Chronos:
    """Get the active global tracer instance."""
    if not _global_tracer:
        init()
    return _global_tracer

__all__ = ["Chronos", "AgentTrace", "AgentSpan", "CheckpointEvent", "init", "step", "tool", "get_tracer"]
