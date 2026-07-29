"""
Chronos adapter for the Strands Agents SDK.

Uses the native Strands lifecycle hook system to automatically record
model calls and tool executions into Chronos traces.

Usage:
    from strands import Agent
    from chronos.core.tracer import Chronos
    from chronos.adapters.strands import ChronosStrandsAdapter

    chronos = Chronos(agent_name="MyStrandsAgent")
    adapter = ChronosStrandsAdapter(chronos)

    agent = Agent(tools=[...])
    adapter.attach(agent)

    with chronos.trace("strands_session"):
        result = agent("What is 2 + 2?")
"""
from typing import Any

try:
    from strands.hooks.events import (
        BeforeModelCallEvent,
        AfterModelCallEvent,
        BeforeToolCallEvent,
        AfterToolCallEvent,
    )
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False


class ChronosStrandsAdapter:
    """
    Chronos adapter for the Strands Agents SDK.
    
    Hooks into the agent's lifecycle events to automatically record:
    - Model calls (before/after)
    - Tool executions (before/after)
    """

    def __init__(self, chronos_instance: Any = None):
        if not STRANDS_AVAILABLE:
            raise ImportError(
                "strands-agents is not installed. "
                "Install it with: pip install strands-agents"
            )
        if chronos_instance is None:
            from chronos import get_tracer
            chronos_instance = get_tracer()
        self.chronos = chronos_instance

    def attach(self, agent: Any) -> None:
        """Attach all Chronos lifecycle hooks to a Strands Agent instance."""
        agent.add_hook(BeforeModelCallEvent, self._on_before_model_call)
        agent.add_hook(AfterModelCallEvent, self._on_after_model_call)
        agent.add_hook(BeforeToolCallEvent, self._on_before_tool_call)
        agent.add_hook(AfterToolCallEvent, self._on_after_tool_call)

    def _on_before_model_call(self, event: "BeforeModelCallEvent") -> None:
        if not self.chronos.current_trace:
            self.chronos.start_trace(name="strands_agent")
        if self.chronos.current_trace:
            # Safely extract messages from the event
            messages = []
            if hasattr(event, 'messages'):
                messages = [str(m)[:200] for m in (event.messages or [])[-3:]]
            self.chronos.checkpoint(
                name="strands_model_call_start",
                state={"messages_tail": messages}
            )

    def _on_after_model_call(self, event: "AfterModelCallEvent") -> None:
        if self.chronos.current_trace:
            output = {}
            if hasattr(event, 'response'):
                output["response_type"] = type(event.response).__name__
            if hasattr(event, 'usage'):
                output["usage"] = str(event.usage)
            self.chronos.checkpoint(
                name="strands_model_call_end",
                state=output
            )

    def _on_before_tool_call(self, event: "BeforeToolCallEvent") -> None:
        if not self.chronos.current_trace:
            self.chronos.start_trace(name="strands_agent")
        if self.chronos.current_trace:
            state = {}
            if hasattr(event, 'tool_name'):
                state["tool_name"] = event.tool_name
            if hasattr(event, 'tool_input'):
                state["tool_input"] = str(event.tool_input)[:500]
            self.chronos.checkpoint(
                name="strands_tool_call_start",
                state=state
            )

    def _on_after_tool_call(self, event: "AfterToolCallEvent") -> None:
        if self.chronos.current_trace:
            state = {}
            if hasattr(event, 'tool_name'):
                state["tool_name"] = event.tool_name
            if hasattr(event, 'tool_result'):
                state["tool_result"] = str(event.tool_result)[:500]
            self.chronos.checkpoint(
                name="strands_tool_call_end",
                state=state
            )
