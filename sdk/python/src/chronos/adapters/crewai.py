from typing import Any, Callable, Dict, Optional
import json

class ChronosCrewAIAdapter:
    """
    Adapter for CrewAI to automatically trace Task executions and Agent steps.
    """
    def __init__(self, chronos_instance: Any):
        self.chronos = chronos_instance
        
    def get_task_callback(self) -> Callable:
        """Returns a callback to be passed as `task_callback` to a Crew."""
        def callback(output: Any):
            # CrewAI Task Output
            trace = self.chronos.current_trace
            if trace:
                safe_output = str(output) if not isinstance(output, dict) else output
                self.chronos.checkpoint(
                    name="crewai_task_complete",
                    state={"task_output": safe_output}
                )
        return callback

    def get_step_callback(self) -> Callable:
        """Returns a callback to be passed as `step_callback` to a Crew."""
        def callback(step_output: Any):
            trace = self.chronos.current_trace
            if trace:
                # Step output might be an AgentAction or dict
                try:
                    safe_output = json.loads(json.dumps(step_output, default=str))
                except Exception:
                    safe_output = str(step_output)
                    
                self.chronos.checkpoint(
                    name="crewai_agent_step",
                    state={"step": safe_output}
                )
        return callback
