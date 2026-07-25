import time
import pytest
import requests
import httpx
from chronos.interceptors.vcr import VCREngine, VCRMode

def test_requests_vcr_interception():
    """Verify that requests library is intercepted and replayed correctly."""
    vcr = VCREngine(mode=VCRMode.RECORD)
    vcr.enable()
    
    resp1 = requests.get("https://jsonplaceholder.typicode.com/todos/3")
    assert resp1.status_code == 200
    
    recorded = vcr.cassettes
    assert len(recorded) == 1
    vcr.disable()
    
    # Replay
    replay_vcr = VCREngine(mode=VCRMode.REPLAY)
    replay_vcr.load_cassettes(recorded)
    replay_vcr.enable()
    
    start = time.time()
    resp2 = requests.get("https://jsonplaceholder.typicode.com/todos/3")
    duration = time.time() - start
    
    assert resp2.status_code == 200
    assert resp1.text == resp2.text
    # Replay should be nearly instantaneous (< 50ms locally)
    assert duration < 0.05
    
    replay_vcr.disable()

@pytest.mark.asyncio
async def test_httpx_async_vcr_interception():
    """Verify that httpx AsyncClient is intercepted and replayed correctly."""
    vcr = VCREngine(mode=VCRMode.RECORD)
    vcr.enable()
    
    async with httpx.AsyncClient() as client:
        resp1 = await client.get("https://jsonplaceholder.typicode.com/todos/4")
    assert resp1.status_code == 200
    
    recorded = vcr.cassettes
    assert len(recorded) == 1
    vcr.disable()
    
    # Replay
    replay_vcr = VCREngine(mode=VCRMode.REPLAY)
    replay_vcr.load_cassettes(recorded)
    replay_vcr.enable()
    
    async with httpx.AsyncClient() as client:
        resp2 = await client.get("https://jsonplaceholder.typicode.com/todos/4")
        
    assert resp2.status_code == 200
    assert resp1.text == resp2.text
    
    replay_vcr.disable()
