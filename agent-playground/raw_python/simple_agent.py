"""
Raw Python + Chronos Integration Test

Demonstrates how to use Chronos to trace a vanilla Python agent using Google GenAI SDK.
"""
import os
import uuid
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from chronos import Chronos
from chronos.interceptors.vcr import VCREngine, VCRMode

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


tracer = Chronos("RawAgent", framework="raw")


@tracer.adapter.tool("web_search")
def search_web(query: str) -> dict:
    """Fetch data from public API."""
    print(f"[Tool] Searching for: {query}")
    resp = requests.get("https://official-joke-api.appspot.com/random_joke")
    data = resp.json()
    return {"joke": f"{data['setup']} - {data['punchline']}"}


@tracer.adapter.step("reasoning")
def analyze_results(search_results: dict) -> str:
    """Analyze the search results using Gemini LLM if key is available, else fallback."""
    print("[Step] Analyzing results...")
    joke = search_results.get("joke", "No joke found")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
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


@tracer.adapter.tool("formatter")
def format_output(analysis: str) -> str:
    """Format the final output."""
    print("[Tool] Formatting output...")
    return f"[Agent Report] {analysis}"


def run_demo():
    print("--- Raw Python + Chronos Integration Test ---")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not is_valid_key(api_key):
        print("\n[!] Running in fallback mode (No valid GEMINI_API_KEY in agent-playground/.env).")



    print("\n>>> RECORD MODE <<<")
    start1 = time.time()
    with VCREngine(mode="record") as vcr:
        with tracer.trace("raw_session"):
            results = search_web("funny joke")
            with tracer.adapter.trace_block("decision_making"):
                analysis = analyze_results(results)
            final = format_output(analysis)
    duration1 = time.time() - start1

    print(f"\nResult (Record): {final}")
    print(f"Record Duration: {duration1:.2f}s")

    cassettes = vcr.cassettes

    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode="replay")
    replay_vcr.load_cassettes(cassettes)
    
    start2 = time.time()
    with replay_vcr:
        with tracer.trace("raw_session"):
            results2 = search_web("funny joke")
            with tracer.adapter.trace_block("decision_making"):
                analysis2 = analyze_results(results2)
            final2 = format_output(analysis2)
    duration2 = time.time() - start2

    print(f"\nResult (Replay): {final2}")
    print(f"Replay Duration: {duration2:.2f}s")

    assert final == final2, f"Mismatch! Record: {final} vs Replay: {final2}"
    print("\nSUCCESS: Raw Python agent perfectly replayed deterministically and network-free!")


if __name__ == "__main__":
    run_demo()
