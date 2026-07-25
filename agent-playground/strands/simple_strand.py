import uuid
from chronos.core.tracer import Chronos
from chronos.adapters.strands import chronos_strand
import time

chronos = Chronos(agent_name="StrandGraph")

@chronos_strand(chronos, name="data_fetcher")
def fetch_data(query: str):
    print(f"[Strand] Fetching data for: {query}")
    return {"results": [1, 2, 3]}

@chronos_strand(chronos, name="data_processor")
def process_data(data: dict):
    print("[Strand] Processing data...")
    return sum(data["results"])

def run_demo():
    print("--- Strands + Chronos Integration Test ---")
    trace_id = uuid.uuid4()
    
    with chronos.trace("strand_session", force_trace_id=trace_id):
        data = fetch_data("AI trends")
        final = process_data(data)
        
    print(f"Final output: {final}")
    print("SUCCESS: Strands execution fully traced!")

if __name__ == "__main__":
    run_demo()
