import random
import uuid
from contextlib import contextmanager

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
    
    try:
        yield
    finally:
        # 5. Restore original states to avoid polluting the rest of the application
        random.setstate(original_random_state)
        uuid.uuid4 = original_uuid4
