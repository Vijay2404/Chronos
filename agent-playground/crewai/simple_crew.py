import os
import sys
from pathlib import Path
from dotenv import load_dotenv

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
from chronos import Chronos
from chronos.interceptors.vcr import VCREngine, VCRMode


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


def run_demo():
    print("--- CrewAI + Chronos Integration Test ---")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not is_valid_key(api_key):
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")
        print("Adapter loaded successfully!")
        return

    # Setup Gemini LLM for CrewAI using litellm provider string
    llm = LLM(model="gemini/gemini-flash-latest", api_key=api_key)

    # Define agents
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

    # Define tasks
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

    # Setup Chronos
    tracer = Chronos("TechCrew", framework="crewai")

    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True,
        process=Process.sequential,
        step_callback=tracer.adapter.get_step_callback(),
        task_callback=tracer.adapter.get_task_callback()
    )

    print("\n>>> RECORD MODE <<<")
    with VCREngine(mode="record") as vcr:
        with tracer.trace("crew_session"):
            result = crew.kickoff()
            print("\nFinal Output (Record):", result)

    cassettes = vcr.cassettes

    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode="replay")
    replay_vcr.load_cassettes(cassettes)
    
    with replay_vcr:
        with tracer.trace("crew_session"):
            result2 = crew.kickoff()
            print("\nFinal Output (Replay):", result2)
    print("\nSUCCESS: Crew perfectly tracked with step and task callbacks using Gemini!")


if __name__ == "__main__":
    run_demo()
