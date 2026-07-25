import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # We will use a public streaming API or just a slow endpoint
        # The HTTPBIN endpoint /stream/{n} streams n lines of JSON
        req = client.build_request("GET", "https://httpbin.org/stream/3")
        resp = await client.send(req, stream=True)
        
        print(f"Status: {resp.status_code}")
        print("Iterating lines...")
        async for line in resp.aiter_lines():
            print(f"Chunk: {line}")
            
if __name__ == "__main__":
    asyncio.run(main())
