import json
from typing import Any, Optional, Dict, Sequence, Tuple

try:
    from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import BaseMessage, message_to_dict
    LANGGRAPH_AVAILABLE = True
except ImportError:
    BaseCheckpointSaver = object
    MemorySaver = object
    LANGGRAPH_AVAILABLE = False


def _serialize_messages(state: Any) -> Any:
    """Helper to convert LangChain messages in the state into pure dicts for JSON serialization."""
    if isinstance(state, dict):
        new_state = {}
        for k, v in state.items():
            if isinstance(v, list):
                new_state[k] = [
                    message_to_dict(msg) if hasattr(msg, "type") and hasattr(msg, "content") else msg 
                    for msg in v
                ]
            elif hasattr(v, "type") and hasattr(v, "content"):
                new_state[k] = message_to_dict(v)
            else:
                new_state[k] = v
        return new_state
    return state


class ChronosCheckpointer(MemorySaver):
    """
    A LangGraph Checkpointer that extends MemorySaver
    and automatically emits `Chronos.step()` events on every state transition.
    """
    
    def __init__(self, chronos: Any = None):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("langgraph is not installed. Run `pip install langgraph` to use this adapter.")
        super().__init__()
        if chronos is None:
            from chronos import get_tracer
            chronos = get_tracer()
        self.chronos = chronos
        
    def put(self, config: Dict[str, Any], checkpoint: "Checkpoint", metadata: "CheckpointMetadata", new_versions: dict) -> Dict[str, Any]:
        # Save to the underlying memory/storage
        result = super().put(config, checkpoint, metadata, new_versions)
        
        # Log to Chronos if a trace is active (or start one)
        if not self.chronos.current_trace:
            self.chronos.start_trace(name="langgraph_agent")
            
        trace = self.chronos.current_trace
        if trace:
            # LangGraph metadata usually contains the node name that just ran
            node_name = metadata.get("step", metadata.get("source", "langgraph_node"))
            
            # Channel values contain the actual graph state
            state_data = checkpoint.get("channel_values", {})
            safe_state = _serialize_messages(state_data)
            
            # Use step logic manually or create an event
            # To keep it simple, we log it as a checkpoint event
            self.chronos.checkpoint(
                name=f"langgraph_node_{node_name}",
                state=safe_state
            )
            
        return result
