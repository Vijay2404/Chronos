from typing import Any, Callable

def chronos_adk_node(chronos_instance: Any, node_name: str):
    """
    Generic adapter for Google ADK nodes or generic agent nodes.
    Wraps execution to record inputs and outputs to the Chronos trace.
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            trace = chronos_instance.current_trace
            if trace:
                chronos_instance.checkpoint(
                    name=f"adk_node_{node_name}_start",
                    state={"inputs": kwargs}
                )
            
            result = func(*args, **kwargs)
            
            if trace:
                chronos_instance.checkpoint(
                    name=f"adk_node_{node_name}_end",
                    state={"outputs": result}
                )
            return result
        return wrapper
    return decorator
