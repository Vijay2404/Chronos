import uuid
import random
from chronos import Chronos

def run_agent_flow(trace_id_seed: uuid.UUID, run_name: str):
    print(f"\n--- Starting {run_name} ---")
    chronos = Chronos(agent_name="DeterministicAgent")
    
    # By forcing the trace_id, we force the deterministic seed
    with chronos.trace(name="decision_flow", force_trace_id=trace_id_seed):
        
        with chronos.step("make_decision"):
            # 1. Randomness is deterministic
            decision = random.choice(["Approve", "Reject", "Needs Review"])
            score = random.random()
            print(f"Random Decision: {decision}")
            print(f"Random Score: {score:.4f}")
            
            # 2. UUID generation is deterministic
            db_id = uuid.uuid4()
            print(f"Generated DB Record ID: {db_id}")
            
            chronos.snapshot(state={"decision": decision, "db_id": str(db_id)})

if __name__ == "__main__":
    # Simulate an original run
    original_trace_id = uuid.uuid4()
    run_agent_flow(trace_id_seed=original_trace_id, run_name="Original Run")
    
    # Simulate a time-travel replay run using the exact same trace_id
    run_agent_flow(trace_id_seed=original_trace_id, run_name="Replay Run (Time Travel)")
