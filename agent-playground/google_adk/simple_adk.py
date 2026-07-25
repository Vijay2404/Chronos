import uuid
from chronos.core.tracer import Chronos
from chronos.adapters.google_adk import chronos_adk_node

chronos = Chronos(agent_name="GoogleADKAgent")

@chronos_adk_node(chronos, node_name="vertex_prompt")
def run_vertex_prompt(prompt: str):
    print(f"[GoogleADK] Running prompt: {prompt}")
    return "This is a simulated response from Google ADK."

def run_demo():
    print("--- Google ADK + Chronos Integration Test ---")
    trace_id = uuid.uuid4()
    
    with chronos.trace("adk_session", force_trace_id=trace_id):
        final = run_vertex_prompt("Hello Google")
        
    print(f"Final output: {final}")
    print("SUCCESS: Google ADK execution fully traced!")

if __name__ == "__main__":
    run_demo()
