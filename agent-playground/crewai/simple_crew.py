import uuid
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from chronos.core.tracer import Chronos
from chronos.adapters.crewai import ChronosCrewAIAdapter
from chronos.interceptors.vcr import VCREngine, VCRMode
import os
import time

def run_demo():
    # Setup LLM - normally requires OPENAI_API_KEY, but we will mock it if possible
    # We can just use a dummy key since VCR engine will capture the requests if we have a real key, 
    # but without a real key we'll get an auth error on RECORD.
    # To run this robustly without tokens, you'd need an existing cassette. 
    # For now, we assume the environment has a valid key for the RECORD pass, or we handle the auth error.
    
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "dummy-key-for-replay-only")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Define agents
    researcher = Agent(
        role='Senior Research Analyst',
        goal='Uncover cutting-edge developments in AI',
        backstory="""You work at a leading tech think tank.
        Your expertise lies in identifying emerging trends.
        You have a knack for dissecting complex data and presenting actionable insights.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer = Agent(
        role='Tech Content Strategist',
        goal='Craft compelling content on tech advancements',
        backstory="""You are a renowned Content Strategist, known for your insightful and engaging articles.
        You transform complex concepts into compelling narratives.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )

    # Define tasks
    task1 = Task(
        description="""Conduct a comprehensive analysis of the latest advancements in AI agents.
        Identify key trends, breakthrough technologies, and potential industry impacts.""",
        expected_output="Full analysis report in bullet points",
        agent=researcher
    )

    task2 = Task(
        description="""Using the insights provided, develop an engaging blog
        post that highlights the most significant AI agent advancements.
        Your post should be informative yet accessible, catering to a tech-savvy audience.""",
        expected_output="Full blog post of at least 4 paragraphs",
        agent=writer
    )

    # Setup Chronos
    chronos = Chronos(agent_name="TechCrew")
    adapter = ChronosCrewAIAdapter(chronos)
    trace_id = uuid.uuid4()

    # Create Crew with adapter callbacks
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True,
        process=Process.sequential,
        step_callback=adapter.get_step_callback(),
        task_callback=adapter.get_task_callback()
    )

    print("--- CrewAI + Chronos Integration Test ---")
    
    # We won't actually execute it against OpenAI unless you have an API key configured.
    # But this script structure perfectly demonstrates the adapter wrapping!
    
    if os.getenv("OPENAI_API_KEY") != "dummy-key-for-replay-only":
        print("\n>>> RECORD MODE <<<")
        vcr = VCREngine(mode=VCRMode.RECORD)
        vcr.enable()
        
        with chronos.trace("crew_session", force_trace_id=trace_id):
            result = crew.kickoff()
            print("Final Output:", result)
            
        vcr.disable()
        cassettes = vcr.cassettes
        
        print("\n>>> REPLAY MODE <<<")
        replay_vcr = VCREngine(mode=VCRMode.REPLAY)
        replay_vcr.load_cassettes(cassettes)
        replay_vcr.enable()
        
        with chronos.trace("crew_session", force_trace_id=trace_id):
            result2 = crew.kickoff()
            print("Final Output (Replay):", result2)
            
        replay_vcr.disable()
        assert str(result) == str(result2)
        print("SUCCESS: Crew perfectly replayed!")
    else:
        print("Set OPENAI_API_KEY to run the full record/replay test. Adapter initialized successfully!")

if __name__ == "__main__":
    run_demo()
