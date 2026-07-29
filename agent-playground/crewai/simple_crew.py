"""
CrewAI + Chronos Integration Test (New DX)
"""
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from crewai import Agent, Task, Crew, Process, LLM

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="TechCrew")

# 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BINDING)
from chronos.adapters.crewai import ChronosCrewAIAdapter


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


def run_demo():
    print("--- CrewAI + Chronos Integration Test ---")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not is_valid_key(api_key):
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")
        return

    llm = LLM(model="gemini/gemini-flash-latest", api_key=api_key)

    researcher = Agent(
        role='Senior Research Analyst',
        goal='Summarize key breakthrough in AI in 1 bullet point',
        backstory="You work at a tech think tank. Concise and accurate.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer = Agent(
        role='Tech Content Strategist',
        goal='Write a 1-sentence summary based on the research',
        backstory="You write ultra-concise summaries.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    task1 = Task(
        description="Identify 1 major AI trend for 2026.",
        expected_output="1 bullet point string",
        agent=researcher
    )

    task2 = Task(
        description="Write a 1-sentence headline based on the trend.",
        expected_output="1 short sentence",
        agent=writer
    )

    # Attach callbacks. The adapter auto-manages trace lifecycles!
    adapter = ChronosCrewAIAdapter()
    
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True,
        process=Process.sequential,
        step_callback=adapter.get_step_callback(),
        task_callback=adapter.get_task_callback()
    )

    start_time = time.time()
    result = crew.kickoff()
    duration = time.time() - start_time
    
    print("\nFinal Output:", result)
    print(f"Duration: {duration:.2f}s")
    print("\nSUCCESS: Crew perfectly tracked!")
    print("[i] Run this with `CHRONOS_REPLAY_MODE=1 python simple_crew.py` to test Replay Mode!")


if __name__ == "__main__":
    run_demo()
