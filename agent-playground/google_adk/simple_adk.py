"""
Google ADK + Chronos Integration Test (New DX)
"""
import os
import time
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="GoogleADKWeatherBot")

# 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BINDING)
from chronos.adapters.google_adk import ChronosADKAdapter

try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


def get_weather(city: str) -> dict:
    """Returns the current weather for a given city."""
    print(f"[Tool] Getting weather for: {city}")
    return {"city": city, "temperature": "22°C", "condition": "Sunny"}


def calculate_sum(a: int, b: int) -> dict:
    """Adds two numbers together."""
    print(f"[Tool] Calculating {a} + {b}")
    return {"result": a + b}


async def run_demo():
    print("--- Google ADK + Chronos Integration Test ---")

    if not ADK_AVAILABLE:
        print("google-adk is not installed. Install with: pip install google-adk")
        return

    # Attach callbacks. The adapter auto-manages trace lifecycles!
    adapter = ChronosADKAdapter()

    agent = Agent(
        name="weather_assistant",
        model="gemini-flash-latest",
        description="A helpful assistant that provides weather information.",
        instruction="You are a weather assistant. Use the get_weather tool when asked about weather. Use calculate_sum for math.",
        tools=[get_weather, calculate_sum],
        **adapter.get_callbacks_dict()
    )
    print("[OK] Google ADK Agent created with Chronos callbacks attached")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if is_valid_key(api_key):
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        
        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name="chronos_test", session_service=session_service)
        
        session = await session_service.create_session(app_name="chronos_test", user_id="test_user")
        
        from google.genai import types
        user_msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in London?")]
        )
        
        response_text = ""
        start_time = time.time()
        
        async for event in runner.run_async(user_id="test_user", session_id=session.id, new_message=user_msg):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                
        duration = time.time() - start_time
                
        print(f"\nFinal Result: {response_text}")
        print(f"Duration: {duration:.2f}s")
        print("\nSUCCESS: Google ADK Agent fully traced!")
        print("[i] Run this with `CHRONOS_REPLAY_MODE=1 python simple_adk.py` to test Replay Mode!")
    else:
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")


if __name__ == "__main__":
    asyncio.run(run_demo())
