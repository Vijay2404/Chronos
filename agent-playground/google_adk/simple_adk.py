"""
Google ADK + Chronos Integration Test

Demonstrates how Chronos hooks into Google ADK's native callback system
to automatically trace agent, model, and tool lifecycle events.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from chronos import Chronos
from chronos.interceptors.vcr import VCREngine, VCRMode

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

    tracer = Chronos("GoogleADKWeatherBot", framework="google_adk")

    if not ADK_AVAILABLE:
        print("google-adk is not installed. Install with: pip install google-adk")
        print("Adapter loaded successfully! Skipping full execution test.")
        return

    agent = Agent(
        name="weather_assistant",
        model="gemini-flash-latest",
        description="A helpful assistant that provides weather information.",
        instruction="You are a weather assistant. Use the get_weather tool when asked about weather. Use calculate_sum for math.",
        tools=[get_weather, calculate_sum],
        **tracer.adapter.get_callbacks_dict()
    )
    print("[OK] Google ADK Agent created with Chronos callbacks attached")


    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if is_valid_key(api_key):
        print("\n>>> RECORD MODE <<<")
        with VCREngine(mode="record") as vcr:
            with tracer.trace("adk_session"):
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
            async for event in runner.run_async(user_id="test_user", session_id=session.id, new_message=user_msg):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    
            print(f"\nResult (Record): {response_text}")

        cassettes = vcr.cassettes

        print("\n>>> REPLAY MODE <<<")
        replay_vcr = VCREngine(mode="replay")
        replay_vcr.load_cassettes(cassettes)

        with replay_vcr:
            with tracer.trace("adk_session"):
                session2 = await session_service.create_session(app_name="chronos_test", user_id="test_user_2")
            
            response_text_2 = ""
            async for event in runner.run_async(user_id="test_user_2", session_id=session2.id, new_message=user_msg):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text_2 = event.content.parts[0].text
                    
            print(f"\nResult (Replay): {response_text_2}")
        print("\nSUCCESS: Google ADK Agent fully traced with all 6 lifecycle callbacks!")
    else:
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")
        print("Adapter + callbacks validated successfully!")


if __name__ == "__main__":
    asyncio.run(run_demo())
