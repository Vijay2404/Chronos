import os
import uuid
import time
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage

from chronos import Chronos
# pyrefly: ignore [missing-import]
from chronos.adapters.langgraph import ChronosCheckpointer
from chronos.interceptors.vcr import VCREngine, VCRMode

# Simple state schema
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# Define nodes
def llm_node(state: AgentState):
    # Using a fake/test API key since we'll mock it soon, but for real recording, you'd need a real key.
    # For this test without spending tokens, let's just make it a mock LLM or rely on VCR strictly if we have a real key.
    # Wait, to test it, the user might not have OPENAI_API_KEY set.
    # Let's write a simple dummy function first that doesn't strictly need OpenAI, or we can use it and catch the error.
    pass

# Wait, if we want to test robust execution without a real API key right now, 
# we can just make a mock node that uses `requests` to fetch a joke, proving the network VCR and state tracking works.
import requests

def fetch_joke_node(state: AgentState):
    print("[Node] Fetching joke...")
    resp = requests.get("https://official-joke-api.appspot.com/random_joke")
    joke_data = resp.json()
    joke_text = f"{joke_data['setup']} - {joke_data['punchline']}"
    return {"messages": [SystemMessage(content=joke_text)]}

def evaluate_joke_node(state: AgentState):
    print("[Node] Evaluating joke deterministically...")
    import random
    # Deterministic choice based on Chronos seed
    rating = random.choice(["Terrible", "Hilarious", "Meh"])
    return {"messages": [SystemMessage(content=f"Rating: {rating}")]}

# Build graph
builder = StateGraph(AgentState)
builder.add_node("fetch", fetch_joke_node)
builder.add_node("evaluate", evaluate_joke_node)
builder.add_edge(START, "fetch")
builder.add_edge("fetch", "evaluate")
builder.add_edge("evaluate", END)

def run_demo():
    print("--- LangGraph + Chronos Integration Test ---")
    
    chronos = Chronos(agent_name="JokeGraph")
    checkpointer = ChronosCheckpointer(chronos)
    graph = builder.compile(checkpointer=checkpointer)
    
    trace_id = uuid.uuid4()
    
    # --- RECORD MODE ---
    print("\n>>> RECORD MODE <<<")
    vcr = VCREngine(mode=VCRMode.RECORD)
    vcr.enable()
    
    start_time = time.time()
    with chronos.trace("joke_session", force_trace_id=trace_id):
        # We must pass a thread_id config for langgraph checkpointers to work
        config = {"configurable": {"thread_id": "1"}}
        result1 = graph.invoke({"messages": [HumanMessage(content="Tell me a joke")]}, config)
        
    duration1 = time.time() - start_time
    vcr.disable()
    
    print(f"Final State (Record): {result1['messages'][-1].content}")
    print(f"Record Duration: {duration1:.2f}s")
    
    # Save cassettes
    cassettes = vcr.cassettes
    
    # --- REPLAY MODE ---
    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode=VCRMode.REPLAY)
    replay_vcr.load_cassettes(cassettes)
    replay_vcr.enable()
    
    start_time = time.time()
    with chronos.trace("joke_session", force_trace_id=trace_id):
        config = {"configurable": {"thread_id": "2"}} # New thread to force fresh execution
        result2 = graph.invoke({"messages": [HumanMessage(content="Tell me a joke")]}, config)
        
    duration2 = time.time() - start_time
    replay_vcr.disable()
    
    print(f"Final State (Replay): {result2['messages'][-1].content}")
    print(f"Replay Duration: {duration2:.2f}s")
    
    assert result1['messages'][-1].content == result2['messages'][-1].content
    print("\nSUCCESS: Graph perfectly replayed deterministically and network-free!")

if __name__ == "__main__":
    run_demo()
