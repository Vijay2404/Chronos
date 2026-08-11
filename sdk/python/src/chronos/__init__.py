import os
import sys
import subprocess
import requests
import time
from typing import Optional, Callable

from chronos.core.tracer import Chronos
from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent
from chronos.interceptors.vcr import VCREngine, VCRMode

_global_tracer: Optional[Chronos] = None
_vcr_engine: Optional[VCREngine] = None

def _ensure_server_running():
    try:
        resp = requests.get("http://localhost:8555/health", timeout=0.5)
        if resp.status_code == 200:
            return
    except requests.exceptions.RequestException:
        pass
        
    print("[Chronos] Local server not running. Starting it on port 8555...")
    # Spawn the server in the background
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "chronos_server.main:app", "--port", "8555"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Wait briefly for it to start
    for _ in range(10):
        try:
            if requests.get("http://localhost:8555/health", timeout=0.5).status_code == 200:
                print("[Chronos] Server successfully started!")
                return
        except Exception:
            time.sleep(0.5)
    print("[Chronos] Warning: Failed to confirm server started.")

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
    else:
        _vcr_engine = VCREngine(mode=VCRMode.RECORD)
        
    _vcr_engine.start()

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
