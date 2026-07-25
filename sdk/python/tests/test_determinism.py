import uuid
import random
import time
from datetime import datetime
from chronos import Chronos

def test_random_and_uuid_determinism():
    """Verify that random module and uuid4 generate identical sequences for the same trace seed."""
    chronos = Chronos(agent_name="TestBot")
    seed = uuid.uuid4()
    
    # Run 1
    with chronos.trace(name="test", force_trace_id=seed):
        decision_1 = random.choice(["A", "B", "C"])
        id_1 = uuid.uuid4()
        score_1 = random.random()
        
    # Run 2 (Time Travel Replay)
    with chronos.trace(name="test", force_trace_id=seed):
        decision_2 = random.choice(["A", "B", "C"])
        id_2 = uuid.uuid4()
        score_2 = random.random()
        
    assert decision_1 == decision_2
    assert id_1 == id_2
    assert score_1 == score_2

def test_time_determinism():
    """Verify that time.time() and datetime.now() tick deterministically."""
    chronos = Chronos(agent_name="TimeBot")
    seed = uuid.uuid4()
    
    # Run 1
    with chronos.trace(name="test", force_trace_id=seed):
        t1_run1 = time.time()
        d1_run1 = datetime.now()
        
        # Simulated logic delay
        time.sleep(0.01)
        
        t2_run1 = time.time()
        d2_run1 = datetime.now()
        
    # Run 2
    with chronos.trace(name="test", force_trace_id=seed):
        t1_run2 = time.time()
        d1_run2 = datetime.now()
        
        time.sleep(0.01)
        
        t2_run2 = time.time()
        d2_run2 = datetime.now()
        
    # Check that time progresses
    assert t2_run1 > t1_run1
    assert d2_run1 > d1_run1
    
    # Check that time logic is perfectly reproducible
    assert t1_run1 == t1_run2
    assert d1_run1 == d1_run2
    assert t2_run1 == t2_run2
    assert d2_run1 == d2_run2
