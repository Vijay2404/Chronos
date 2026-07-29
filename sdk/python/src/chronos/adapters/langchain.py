from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class ChronosLangchainCallback(BaseCallbackHandler):
    """
    Chronos callback handler for LangChain.
    Automatically records LLM, Chain, and Tool executions into the Chronos trace.
    """
    def __init__(self, chronos_instance: Any = None):
        super().__init__()
        if chronos_instance is None:
            from chronos import get_tracer
            chronos_instance = get_tracer()
        self.chronos = chronos_instance
        self._auto_started_trace = False

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_llm_start",
                state={"prompts": prompts}
            )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        trace = self.chronos.current_trace
        if trace:
            outputs = [[gen.text for gen in gens] for gens in response.generations]
            self.chronos.checkpoint(
                name="langchain_llm_end",
                state={"outputs": outputs}
            )

    def on_chain_start(
        self, serialized: Optional[Dict[str, Any]], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        if not self.chronos.current_trace:
            name = serialized.get("name", "langchain_agent") if serialized else "langchain_agent"
            self.chronos.start_trace(name=name)
            self._auto_started_trace = True
            
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_chain_start",
                state={"inputs": inputs}
            )

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        trace = self.chronos.current_trace
        if trace:
            # Safely serialize outputs to avoid JSON serialization errors
            safe_outputs = {}
            if isinstance(outputs, dict):
                for k, v in outputs.items():
                    if hasattr(v, "content"):
                        safe_outputs[k] = v.content
                    elif hasattr(v, "text"):
                        safe_outputs[k] = v.text
                    elif isinstance(v, (str, int, float, bool, type(None))):
                        safe_outputs[k] = v
                    else:
                        safe_outputs[k] = str(v)
            else:
                safe_outputs = {"result": str(outputs)}
                
            self.chronos.checkpoint(
                name="langchain_chain_end",
                state={"outputs": safe_outputs}
            )
            if self._auto_started_trace:
                # To prevent closing on nested chains, we should be careful, 
                # but for simplicity we assume the root chain ends last.
                # Actually, langchain fires on_chain_end multiple times. 
                # Better to just not close it here or check if it's the root run.
                # If we don't end it, it's fine. We can just leave the trace open.
                # Or we can end it if kwargs doesn't have parent_run_id.
                parent_run_id = kwargs.get("parent_run_id")
                if parent_run_id is None:
                    self.chronos.end_trace()
                    self._auto_started_trace = False

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_tool_start",
                state={"tool_input": input_str, "tool": serialized.get("name", "unknown")}
            )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_tool_end",
                state={"tool_output": output}
            )
