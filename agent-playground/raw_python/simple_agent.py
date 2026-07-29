"""
Raw Python + Chronos Integration Test (New DX)

Demonstrates how to use Chronos to trace a vanilla Python agent using Google GenAI SDK.
"""
import os
import time
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="RawAgent")
from chronos import step, tool, get_tracer

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))

# 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BOUNDARIES)
@tool("web_search")
def search_web(query: str) -> dict:
    """Fetch data from public API."""
    print(f"[Tool] Searching for: {query}")
    resp = requests.get("https://official-joke-api.appspot.com/random_joke")
    data = resp.json()
    return {"joke": f"{data['setup']} - {data['punchline']}"}


@step("reasoning")
def analyze_results(search_results: dict) -> str:
    """Analyze the search results using Gemini LLM if key is available, else fallback."""
    print("[Step] Analyzing results...")
    joke = search_results.get("joke", "No joke found")

    api_key = os.getenv("GOOGLE_API_KEY")
    if is_valid_key(api_key) and GENAI_AVAILABLE:
        client = genai.Client(api_key=api_key)
        prompt = f"Analyze this joke and explain why it's funny in 1 short sentence: {joke}"
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return response.text.strip()
    else:
        word_count = len(joke.split())
        return f"Deterministic joke analysis ({word_count} words): {joke}"


@tool("formatter")
def format_output(analysis: str) -> str:
    """Format the final output."""
    print("[Tool] Formatting output...")
    return f"[Agent Report] {analysis}"


def run_demo():
    print("--- Raw Python + Chronos Integration Test ---")
    
    start1 = time.time()
    
    # We optionally group these steps into one single session trace
    with get_tracer().trace("raw_session"):
        results = search_web("funny joke")
        analysis = analyze_results(results)
        final = format_output(analysis)
        
    duration1 = time.time() - start1

    print(f"\nResult: {final}")
    print(f"Duration: {duration1:.2f}s")
    
    print("\n[i] Run this with `CHRONOS_REPLAY_MODE=1 python simple_agent.py` to test Replay Mode!")

if __name__ == "__main__":
    run_demo()
