from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, UUID4

class AgentEvent(BaseModel):
    """Base model for all events in the Chronos system."""
    id: UUID4
    trace_id: UUID4
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    name: str

class AgentSpan(AgentEvent):
    """Represents a specific step in an agent's execution (e.g., an LLM call or a Tool call)."""
    span_id: UUID4
    parent_span_id: Optional[UUID4] = None
    span_type: str = Field(description="e.g., 'llm', 'tool', 'reasoning'")
    status: str = Field(description="'success' or 'error'")
    
    # Inputs and outputs can be any JSON-serializable structure
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Optional[Dict[str, Any]] = None
    
    # Specific to LLMs
    token_usage: Optional[Dict[str, int]] = None
    
    # Execution time
    end_timestamp: Optional[datetime] = None
    duration_ms: Optional[float] = None

class CheckpointEvent(AgentEvent):
    """Represents a snapshot of the agent's internal state at a specific point in time."""
    span_id: UUID4
    state_blob: Any = Field(description="The serialized state. Can be JSON or binary if using cloudpickle.")
    is_binary: bool = Field(default=False, description="True if state_blob is pickled binary data.")

class AgentTrace(BaseModel):
    """Represents a full execution run of an agent."""
    trace_id: UUID4
    name: str = Field(description="Name of the agent or task")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = Field(description="'running', 'success', 'error'")
    
    # Metadata for the run (e.g., framework used, python version, etc)
    metadata: Dict[str, Any] = Field(default_factory=dict)
