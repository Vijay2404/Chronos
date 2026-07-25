# Scratch script to test the VCR stream wrapping logic
import asyncio
import httpx

class VCRAsyncStreamWrapper(httpx.AsyncByteStream):
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
        await self.original_stream.aclose()

async def main():
    def save_cassette(body_bytes):
        print(f"\n[VCR] Stream finished! Saving cassette with {len(body_bytes)} bytes")
        print(f"[VCR] Body: {body_bytes.decode('utf-8', errors='replace')[:50]}...")

    async with httpx.AsyncClient() as client:
        req = client.build_request("GET", "https://jsonplaceholder.typicode.com/todos/1")
        resp = await client.send(req, stream=True)
        
        # Wrap the stream
        resp.stream = VCRAsyncStreamWrapper(resp.stream, save_cassette)
        
        print("Iterating...")
        async for chunk in resp.aiter_bytes():
            print(f"Got chunk: {len(chunk)} bytes")

if __name__ == "__main__":
    asyncio.run(main())
