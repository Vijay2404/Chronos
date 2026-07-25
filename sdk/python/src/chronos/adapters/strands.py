from functools import wraps
from typing import Any, Callable

def chronos_strand(chronos_instance: Any, name: str = "strand_execution"):
    """
    A generic decorator for Strands architecture to trace function execution
    and emit checkpoint events automatically.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace = chronos_instance.current_trace
            if trace:
                chronos_instance.checkpoint(
                    name=f"{name}_start",
                    state={"args": args, "kwargs": kwargs}
                )
                
            result = func(*args, **kwargs)
            
            if trace:
                chronos_instance.checkpoint(
                    name=f"{name}_end",
                    state={"result": result}
                )
            return result
        return wrapper
    return decorator
