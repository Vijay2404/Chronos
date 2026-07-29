"""
Chronos adapter for raw Python agents (no framework).

Provides simple decorators and context managers for tracing vanilla Python
functions as agent steps, tool calls, or LLM interactions — without requiring
any external agent framework.

Usage:
    from chronos.core.tracer import Chronos
    from chronos.adapters.raw_python import ChronosRawAdapter

    chronos = Chronos(agent_name="MyVanillaAgent")
    adapter = ChronosRawAdapter(chronos)

    @adapter.tool("calculator")
    def add(a, b):
        return a + b

    @adapter.llm_call("openai_gpt4")
    def call_llm(prompt):
        return openai.chat(prompt)

    with chronos.trace("session"):
        result = add(1, 2)
        response = call_llm("Hello")
"""
from functools import wraps
from typing import Any, Callable, Optional
from contextlib import contextmanager


class ChronosRawAdapter:
    """
    Lightweight adapter for tracing vanilla Python agent code with Chronos.
    
    Provides decorators to mark functions as specific agent lifecycle events:
    - @adapter.tool(name)       — wraps a tool/function call
    - @adapter.llm_call(name)   — wraps an LLM API call
    - @adapter.step(name)       — wraps a generic agent step (reasoning, planning, etc.)
    """

    def __init__(self, chronos_instance: Any):
        self.chronos = chronos_instance

    def tool(self, name: str = "tool"):
        """Decorator to trace a function as a tool execution."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace = self.chronos.current_trace
                if trace:
                    self.chronos.checkpoint(
                        name=f"tool_{name}_start",
                        state={
                            "function": func.__name__,
                            "args": _safe_serialize(args),
                            "kwargs": _safe_serialize(kwargs)
                        }
                    )

                result = func(*args, **kwargs)

                if trace:
                    self.chronos.checkpoint(
                        name=f"tool_{name}_end",
                        state={
                            "function": func.__name__,
                            "result": _safe_serialize(result)
                        }
                    )
                return result
            return wrapper
        return decorator

    def llm_call(self, name: str = "llm"):
        """Decorator to trace a function as an LLM API call."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace = self.chronos.current_trace
                if trace:
                    self.chronos.checkpoint(
                        name=f"llm_{name}_start",
                        state={
                            "function": func.__name__,
                            "args": _safe_serialize(args),
                            "kwargs": _safe_serialize(kwargs)
                        }
                    )

                result = func(*args, **kwargs)

                if trace:
                    self.chronos.checkpoint(
                        name=f"llm_{name}_end",
                        state={
                            "function": func.__name__,
                            "result": _safe_serialize(result)
                        }
                    )
                return result
            return wrapper
        return decorator

    def step(self, name: str = "step"):
        """Decorator to trace a function as a generic agent step."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace = self.chronos.current_trace
                if trace:
                    self.chronos.checkpoint(
                        name=f"step_{name}_start",
                        state={
                            "function": func.__name__,
                            "args": _safe_serialize(args),
                            "kwargs": _safe_serialize(kwargs)
                        }
                    )

                result = func(*args, **kwargs)

                if trace:
                    self.chronos.checkpoint(
                        name=f"step_{name}_end",
                        state={
                            "function": func.__name__,
                            "result": _safe_serialize(result)
                        }
                    )
                return result
            return wrapper
        return decorator

    @contextmanager
    def trace_block(self, name: str, metadata: Optional[dict] = None):
        """Context manager to trace an arbitrary block of code as a named step."""
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name=f"block_{name}_start",
                state={"metadata": metadata or {}}
            )
        try:
            yield
        finally:
            if trace:
                self.chronos.checkpoint(
                    name=f"block_{name}_end",
                    state={"metadata": metadata or {}}
                )


def _safe_serialize(obj: Any) -> Any:
    """Safely convert objects to JSON-friendly representations."""
    try:
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        if isinstance(obj, (list, tuple)):
            return [_safe_serialize(item) for item in obj[:10]]  # cap at 10 items
        if isinstance(obj, dict):
            return {str(k): _safe_serialize(v) for k, v in list(obj.items())[:20]}
        return str(obj)[:500]
    except Exception:
        return "<unserializable>"
