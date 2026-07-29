"""
Chronos adapter for the Google Agent Development Kit (ADK).

Uses the native ADK callback system (before_agent, after_agent, before_model,
after_model, before_tool, after_tool) to automatically record agent lifecycle
events into Chronos traces.
"""
from typing import Any, Optional


class ChronosADKAdapter:
    """
    Chronos adapter for Google ADK.
    """

    def __init__(self, chronos_instance: Any = None):
        if chronos_instance is None:
            from chronos import get_tracer
            chronos_instance = get_tracer()
        self.chronos = chronos_instance
        self._auto_started_trace = False

    def before_agent(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called before the agent starts processing."""
        if not self.chronos.current_trace:
            self.chronos.start_trace(name="adk_agent")
            self._auto_started_trace = True
            
        if self.chronos.current_trace:
            callback_context = kwargs.get("callback_context") or (args[0] if args else None)
            state = {}
            if hasattr(callback_context, 'user_content'):
                state["user_content"] = str(callback_context.user_content)[:500]
            if hasattr(callback_context, 'agent_name'):
                state["agent_name"] = callback_context.agent_name
            self.chronos.checkpoint(
                name="adk_agent_start",
                state=state
            )
        return None

    def after_agent(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called after the agent finishes processing."""
        if self.chronos.current_trace:
            callback_context = kwargs.get("callback_context") or (args[0] if args else None)
            state = {}
            if hasattr(callback_context, 'state'):
                try:
                    state["session_state"] = dict(callback_context.state)
                except Exception:
                    state["session_state"] = str(callback_context.state)[:500]
            self.chronos.checkpoint(
                name="adk_agent_end",
                state=state
            )
            if self._auto_started_trace:
                self.chronos.end_trace()
                self._auto_started_trace = False
        return None

    def before_model(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called before sending a request to the LLM."""
        if self.chronos.current_trace:
            llm_request = kwargs.get("llm_request") or (args[1] if len(args) > 1 else None)
            state = {"event": "model_call_start"}
            if hasattr(llm_request, 'contents'):
                state["prompt_length"] = len(llm_request.contents) if llm_request.contents else 0
            self.chronos.checkpoint(
                name="adk_model_call_start",
                state=state
            )
        return None

    def after_model(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called after receiving a response from the LLM."""
        if self.chronos.current_trace:
            llm_response = kwargs.get("llm_response") or (args[1] if len(args) > 1 else None)
            state = {"event": "model_call_end"}
            if hasattr(llm_response, 'content'):
                state["response_preview"] = str(llm_response.content)[:300]
            if hasattr(llm_response, 'usage_metadata'):
                state["usage"] = str(llm_response.usage_metadata)
            self.chronos.checkpoint(
                name="adk_model_call_end",
                state=state
            )
        return None

    def before_tool(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called before executing a tool."""
        if self.chronos.current_trace:
            tool_name = kwargs.get("tool_name") or kwargs.get("name") or (args[1] if len(args) > 1 else "unknown_tool")
            tool_args = kwargs.get("tool_args") or kwargs.get("args") or (args[2] if len(args) > 2 else {})
            self.chronos.checkpoint(
                name="adk_tool_call_start",
                state={
                    "tool_name": str(tool_name),
                    "tool_args": str(tool_args)[:500]
                }
            )
        return None

    def after_tool(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Called after a tool finishes executing."""
        if self.chronos.current_trace:
            tool_name = kwargs.get("tool_name") or kwargs.get("name") or (args[1] if len(args) > 1 else "unknown_tool")
            tool_response = kwargs.get("tool_response") or kwargs.get("response") or (args[3] if len(args) > 3 else None)
            self.chronos.checkpoint(
                name="adk_tool_call_end",
                state={
                    "tool_name": str(tool_name),
                    "tool_result": str(tool_response)[:500]
                }
            )
        return None

    def get_callbacks_dict(self) -> dict:
        """Returns a dict of all callbacks, ready to be unpacked into Agent(...)."""
        return {
            "before_agent_callback": self.before_agent,
            "after_agent_callback": self.after_agent,
            "before_model_callback": self.before_model,
            "after_model_callback": self.after_model,
            "before_tool_callback": self.before_tool,
            "after_tool_callback": self.after_tool,
        }
