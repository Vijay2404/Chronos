import enum
import hashlib
import logging
import urllib.request
import urllib.error
import json
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class VCRAsyncStreamWrapper:
    """Wraps an httpx.AsyncByteStream to record chunks as they are consumed."""
    def __init__(self, original_stream, on_complete):
        self.original_stream = original_stream
        self.on_complete = on_complete
        self.buffer = bytearray()
        
    async def __aiter__(self):
        async for chunk in self.original_stream:
            self.buffer.extend(chunk)
            yield chunk
        self.on_complete(bytes(self.buffer))
        
    async def aclose(self):
        if hasattr(self.original_stream, "aclose"):
            await self.original_stream.aclose()

logger = logging.getLogger("chronos.vcr")

class VCRMode(str, enum.Enum):
    RECORD = "RECORD"
    REPLAY = "REPLAY"
    PASSTHROUGH = "PASSTHROUGH"

class VCRRequest(BaseModel):
    method: str
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None

class VCRResponse(BaseModel):
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: str
    duration_ms: float = 0.0

class VCRCassette(BaseModel):
    request: VCRRequest
    response: VCRResponse

class VCREngine:
    """VCR Engine for recording and replaying HTTP interactions."""

    def __init__(self, mode: Union[VCRMode, str] = VCRMode.RECORD):
        if isinstance(mode, str):
            mode = VCRMode(mode.upper())
        self.mode = mode
        self._original_requests_send = None
        self._original_httpx_send = None
        self._original_httpx_async_send = None
        self._is_active = False

    def load_cassettes(self, cassettes: List[VCRCassette]):
        pass  # Deprecated in Phase 4: Server handles storage

    def _save_cassette_to_server(self, cassette: VCRCassette):
        cassette_dict = cassette.model_dump()
        cassette_dict["hash"] = self._hash_request(cassette.request.method, cassette.request.url, cassette.request.body)
        req = urllib.request.Request(
            "http://localhost:8555/api/cassettes", 
            data=json.dumps(cassette_dict).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}, 
            method="POST"
        )
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            logger.warning(f"[Chronos VCR] Failed to save cassette to server: {e}")

    def _fetch_cassette_from_server(self, target_hash: str) -> Optional[VCRCassette]:
        req = urllib.request.Request(f"http://localhost:8555/api/cassettes/{target_hash}", method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return VCRCassette(**data)
        except urllib.error.HTTPError as e:
            return None
        except Exception as e:
            logger.warning(f"[Chronos VCR] Failed to fetch cassette from server: {e}")
            return None

    def _hash_request(self, method: str, url: str, body: Optional[str]) -> str:
        """Generate a matching hash for request matching during replay."""
        raw = f"{method.upper()}:{url}:{body or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def start(self):
        """Enable HTTP monkey-patching for the requests library."""
        if self._is_active:
            return

        try:
            import requests.sessions
            self._original_requests_send = requests.sessions.Session.send
            
            engine_self = self
            
            def patched_requests_send(session_self, request, **kwargs):
                if engine_self.mode == VCRMode.PASSTHROUGH:
                    return engine_self._original_requests_send(session_self, request, **kwargs)

                req_url = request.url
                req_method = request.method
                req_body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body

                if engine_self.mode == VCRMode.RECORD:
                    resp = engine_self._original_requests_send(session_self, request, **kwargs)
                    vcr_req = VCRRequest(method=req_method, url=req_url, body=req_body)
                    vcr_resp = VCRResponse(status_code=resp.status_code, headers=dict(resp.headers), body=resp.text)
                    cassette = VCRCassette(request=vcr_req, response=vcr_resp)
                    engine_self._save_cassette_to_server(cassette)
                    logger.info(f"[Chronos VCR] Recorded requests {req_method} {req_url} -> {resp.status_code}")
                    return resp

                elif engine_self.mode == VCRMode.REPLAY:
                    target_hash = engine_self._hash_request(req_method, req_url, req_body)
                    cassette = engine_self._fetch_cassette_from_server(target_hash)
                    
                    if cassette:
                        logger.info(f"[Chronos VCR] Replaying cached requests {req_method} {req_url} (0ms, 0 tokens)")
                        synth_resp = requests.Response()
                        synth_resp.status_code = cassette.response.status_code
                        synth_resp._content = cassette.response.body.encode("utf-8")
                        
                        # Remove compression headers since we return uncompressed string bytes
                        headers = dict(cassette.response.headers)
                        headers.pop("Content-Encoding", None)
                        headers.pop("content-encoding", None)
                        headers.pop("Content-Length", None)
                        headers.pop("content-length", None)
                        
                        synth_resp.headers.update(headers)
                        synth_resp.url = req_url
                        return synth_resp
                        
                    raise RuntimeError(f"[Chronos VCR] No cached cassette found for REPLAY of {req_method} {req_url}")

            requests.sessions.Session.send = patched_requests_send
        except ImportError:
            logger.warning("[Chronos VCR] 'requests' library not found.")

        # --- HTTPX Patching (Sync and Async) ---
        try:
            import httpx
            
            self._original_httpx_send = httpx.Client.send
            self._original_httpx_async_send = httpx.AsyncClient.send
            
            def patched_httpx_send(client_self, request, **kwargs):
                if engine_self.mode == VCRMode.PASSTHROUGH:
                    return engine_self._original_httpx_send(client_self, request, **kwargs)
                
                req_url = str(request.url)
                req_method = request.method
                req_body = request.read().decode("utf-8") if request.stream else None
                
                if engine_self.mode == VCRMode.RECORD:
                    resp = engine_self._original_httpx_send(client_self, request, **kwargs)
                    # We must read the response to cache it
                    resp.read()
                    vcr_req = VCRRequest(method=req_method, url=req_url, body=req_body)
                    vcr_resp = VCRResponse(status_code=resp.status_code, headers=dict(resp.headers), body=resp.text)
                    cassette = VCRCassette(request=vcr_req, response=vcr_resp)
                    engine_self._save_cassette_to_server(cassette)
                    logger.info(f"[Chronos VCR] Recorded httpx {req_method} {req_url} -> {resp.status_code}")
                    return resp
                    
                elif engine_self.mode == VCRMode.REPLAY:
                    target_hash = engine_self._hash_request(req_method, req_url, req_body)
                    cassette = engine_self._fetch_cassette_from_server(target_hash)
                    if cassette:
                        logger.info(f"[Chronos VCR] Replaying cached httpx {req_method} {req_url} (0ms, 0 tokens)")
                        
                        headers = dict(cassette.response.headers)
                        headers.pop("Content-Encoding", None)
                        headers.pop("content-encoding", None)
                        headers.pop("Content-Length", None)
                        headers.pop("content-length", None)
                        
                        return httpx.Response(
                            status_code=cassette.response.status_code,
                            headers=httpx.Headers(headers),
                            content=cassette.response.body.encode("utf-8"),
                            request=request
                        )
                    raise RuntimeError(f"[Chronos VCR] No cached cassette found for REPLAY of {req_method} {req_url}. Hash: {target_hash}")

            async def patched_httpx_async_send(client_self, request, **kwargs):
                if engine_self.mode == VCRMode.PASSTHROUGH:
                    return await engine_self._original_httpx_async_send(client_self, request, **kwargs)
                
                req_url = str(request.url)
                req_method = request.method
                req_body = request.read().decode("utf-8") if request.stream else None
                
                if engine_self.mode == VCRMode.RECORD:
                    resp = await engine_self._original_httpx_async_send(client_self, request, **kwargs)
                    
                    if kwargs.get('stream', False):
                        # Streaming response: wrap the stream and save cassette when it finishes
                        def on_stream_complete(body_bytes: bytes):
                            vcr_req = VCRRequest(method=req_method, url=req_url, body=req_body)
                            # Remove compression headers so replay doesn't crash
                            headers = dict(resp.headers)
                            headers.pop("Content-Encoding", None)
                            headers.pop("content-encoding", None)
                            vcr_resp = VCRResponse(status_code=resp.status_code, headers=headers, body=body_bytes.decode("utf-8", errors="replace"))
                            cassette = VCRCassette(request=vcr_req, response=vcr_resp)
                            engine_self._save_cassette_to_server(cassette)
                            logger.info(f"[Chronos VCR] Recorded httpx async STREAM {req_method} {req_url} -> {resp.status_code} ({len(body_bytes)} bytes)")
                        
                        resp.stream = VCRAsyncStreamWrapper(resp.stream, on_stream_complete)
                        return resp
                    else:
                        # Standard sync response
                        await resp.aread()
                        vcr_req = VCRRequest(method=req_method, url=req_url, body=req_body)
                        vcr_resp = VCRResponse(status_code=resp.status_code, headers=dict(resp.headers), body=resp.text)
                        cassette = VCRCassette(request=vcr_req, response=vcr_resp)
                        engine_self._save_cassette_to_server(cassette)
                        logger.info(f"[Chronos VCR] Recorded httpx async {req_method} {req_url} -> {resp.status_code}")
                        return resp
                    
                elif engine_self.mode == VCRMode.REPLAY:
                    target_hash = engine_self._hash_request(req_method, req_url, req_body)
                    cassette = engine_self._fetch_cassette_from_server(target_hash)
                    if cassette:
                        logger.info(f"[Chronos VCR] Replaying cached httpx async {req_method} {req_url} (0ms, 0 tokens)")
                        
                        headers = dict(cassette.response.headers)
                        headers.pop("Content-Encoding", None)
                        headers.pop("content-encoding", None)
                        headers.pop("Content-Length", None)
                        headers.pop("content-length", None)
                        
                        return httpx.Response(
                            status_code=cassette.response.status_code,
                            headers=httpx.Headers(headers),
                            content=cassette.response.body.encode("utf-8"),
                            request=request
                        )
                    raise RuntimeError(f"[Chronos VCR] No cached cassette found for REPLAY of {req_method} {req_url}")

            httpx.Client.send = patched_httpx_send
            httpx.AsyncClient.send = patched_httpx_async_send
            
        except ImportError:
            logger.warning("[Chronos VCR] 'httpx' library not found. Async LLM interception disabled.")

        self._is_active = True
        logger.info(f"[Chronos VCR] Enabled in {self.mode.value} mode")

    def stop(self):
        """Restore original unpatched functions."""
        if not self._is_active:
            return

        try:
            import requests.sessions
            if self._original_requests_send:
                requests.sessions.Session.send = self._original_requests_send
        except ImportError:
            pass
            
        try:
            import httpx
            if self._original_httpx_send:
                httpx.Client.send = self._original_httpx_send
            if self._original_httpx_async_send:
                httpx.AsyncClient.send = self._original_httpx_async_send
        except ImportError:
            pass

        self._is_active = False
        logger.info("[Chronos VCR] Stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
