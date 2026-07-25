from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class ChronosLangchainCallback(BaseCallbackHandler):
    """
    Chronos callback handler for LangChain.
    Automatically records LLM, Chain, and Tool executions into the Chronos trace.
    """
    def __init__(self, chronos_instance: Any):
        super().__init__()
        self.chronos = chronos_instance

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
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_chain_start",
                state={"inputs": inputs}
            )

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        trace = self.chronos.current_trace
        if trace:
            self.chronos.checkpoint(
                name="langchain_chain_end",
                state={"outputs": outputs}
            )

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
