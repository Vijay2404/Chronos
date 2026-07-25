import random
import uuid
from contextlib import contextmanager
try:
    from freezegun import freeze_time
except ImportError:
    freeze_time = None

@contextmanager
def deterministic_context(seed_str: str):
    """
    Context manager that forces deterministic behavior for:
    - the global `random` module
    - `uuid.uuid4()`
    
    It uses the provided seed_str to initialize deterministic random generation
    and temporarily monkey-patches `uuid.uuid4` to use it instead of `os.urandom`.
    """
    # 1. Save the original states and functions
    original_random_state = random.getstate()
    original_uuid4 = uuid.uuid4
    
    # 2. Seed the global random module
    random.seed(seed_str)
    
    # We maintain a separate Random instance specifically for UUID generation
    # so that user calls to random.random() don't desync UUID sequences
    # if they happen in a different order in a branched trace.
    uuid_random = random.Random(seed_str + "_uuid")
    
    # 3. Create a deterministic uuid4 function
    def deterministic_uuid4():
        # Generate 16 random bytes
        rand_bytes = bytearray(uuid_random.getrandbits(8) for _ in range(16))
        
        # Set the UUIDv4 version (4) and variant (RFC 4122) bits
        rand_bytes[6] = (rand_bytes[6] & 0x0f) | 0x40
        rand_bytes[8] = (rand_bytes[8] & 0x3f) | 0x80
        
        return uuid.UUID(bytes=bytes(rand_bytes))

    # 4. Monkey-patch the standard library
    uuid.uuid4 = deterministic_uuid4
    
    # 5. Lock Time (if freezegun is available)
    # We use the trace_id as a seed to pick a random starting time in the year 2024,
    # and tick=True ensures time moves forward slightly on every time.time() call
    # so we don't break timeouts or loops relying on moving time.
    time_freezer = None
    if freeze_time:
        # Generate a deterministic starting date string
        # using the random instance seeded by the trace_id
        start_year = 2024
        start_month = uuid_random.randint(1, 12)
        start_day = uuid_random.randint(1, 28)
        start_hour = uuid_random.randint(0, 23)
        start_minute = uuid_random.randint(0, 59)
        start_date = f"{start_year}-{start_month:02d}-{start_day:02d} {start_hour:02d}:{start_minute:02d}:00"
        
        # auto_tick_seconds ensures time moves forward by exactly X seconds on every call
        # to time.time() or datetime.now(), making it 100% reproducible regardless of real execution speed.
        time_freezer = freeze_time(start_date, auto_tick_seconds=0.01)
        time_freezer.start()
    
    try:
        yield
    finally:
        # 6. Restore original states to avoid polluting the rest of the application
        if time_freezer:
            time_freezer.stop()
            
        random.setstate(original_random_state)
        uuid.uuid4 = original_uuid4
