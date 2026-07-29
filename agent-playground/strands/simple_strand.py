"""
Strands Agents + Chronos Integration Test

Demonstrates how Chronos hooks into the Strands Agent lifecycle
to automatically trace model calls and tool executions.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Prevent the "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" warning
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

from chronos import Chronos
from chronos.interceptors.vcr import VCREngine

from strands import Agent, tool
from strands.models.gemini import GeminiModel

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    print(f"[Tool] Adding {a} + {b}")
    return a + b

@tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    print(f"[Tool] Multiplying {a} * {b}")
    return a * b


def run_demo():
    print("--- Strands Agents + Chronos Integration Test ---")

    tracer = Chronos("StrandsCalcAgent", framework="strands")

    model = GeminiModel(model_id="gemini-2.5-flash")
    agent = Agent(model=model, tools=[add_numbers, multiply_numbers])
    tracer.adapter.attach(agent)
    print("[OK] Chronos hooks attached to Strands Agent")

    print("\n>>> RECORD MODE <<<")
    with VCREngine(mode="record") as vcr:
        with tracer.trace("strand_session"):
            result = agent("What is 15 + 27? Then multiply the result by 3.")
            print(f"Result (Record): {result}")

    cassettes = vcr.cassettes

    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode="replay")
    replay_vcr.load_cassettes(cassettes)
    
    with replay_vcr:
        with tracer.trace("strand_session"):
            result2 = agent("What is 15 + 27? Then multiply the result by 3.")
            print(f"\nResult (Replay): {result2}")
        print("\nSUCCESS: Strands Agent fully traced with model + tool lifecycle hooks!")


if __name__ == "__main__":
    run_demo()
