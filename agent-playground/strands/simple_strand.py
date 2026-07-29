"""
Strands Agents + Chronos Integration Test (New DX)
"""
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Prevent the "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" warning
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="StrandsCalcAgent")

# 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BINDING)
from chronos.adapters.strands import ChronosStrandsAdapter

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

    model = GeminiModel(model_id="gemini-2.5-flash")
    agent = Agent(model=model, tools=[add_numbers, multiply_numbers])
    
    # Attach callbacks. The adapter auto-manages trace lifecycles!
    adapter = ChronosStrandsAdapter()
    adapter.attach(agent)
    print("[OK] Chronos hooks attached to Strands Agent")

    start_time = time.time()
    result = agent("What is 15 + 27? Then multiply the result by 3.")
    duration = time.time() - start_time
    
    print(f"\nFinal Result: {result}")
    print(f"Duration: {duration:.2f}s")

    print("\nSUCCESS: Strands Agent fully traced!")
    print("[i] Run this with `CHRONOS_REPLAY_MODE=1 python simple_strand.py` to test Replay Mode!")


if __name__ == "__main__":
    run_demo()
