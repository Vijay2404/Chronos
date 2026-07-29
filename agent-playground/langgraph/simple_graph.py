import os
import uuid
import time
from pathlib import Path
from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage

from chronos import Chronos
from chronos.interceptors.vcr import VCREngine, VCRMode

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


def create_graph(use_gemini: bool):
    builder = StateGraph(AgentState)

    if use_gemini and GEMINI_AVAILABLE:
        llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

        def llm_generate_node(state: AgentState):
            print("[Node] Calling Gemini model...")
            response = llm.invoke(state["messages"])
            return {"messages": [response]}

        def summarize_node(state: AgentState):
            print("[Node] Summarizing via Gemini...")
            prompt = [HumanMessage(content=f"Summarize this in 3 words: {state['messages'][-1].content}")]
            summary = llm.invoke(prompt)
            return {"messages": [summary]}

        builder.add_node("llm", llm_generate_node)
        builder.add_node("summarize", summarize_node)
        builder.add_edge(START, "llm")
        builder.add_edge("llm", "summarize")
        builder.add_edge("summarize", END)
    else:
        import requests
        def fetch_joke_node(state: AgentState):
            print("[Node] Fetching joke...")
            resp = requests.get("https://official-joke-api.appspot.com/random_joke")
            joke_data = resp.json()
            joke_text = f"{joke_data['setup']} - {joke_data['punchline']}"
            return {"messages": [SystemMessage(content=joke_text)]}

        def evaluate_joke_node(state: AgentState):
            print("[Node] Evaluating joke...")
            return {"messages": [SystemMessage(content="Rating: Hilarious")]}

        builder.add_node("fetch", fetch_joke_node)
        builder.add_node("evaluate", evaluate_joke_node)
        builder.add_edge(START, "fetch")
        builder.add_edge("fetch", "evaluate")
        builder.add_edge("evaluate", END)

    return builder


def run_demo():
    print("--- LangGraph + Chronos Integration Test ---")

    tracer = Chronos("JokeGraph", framework="langgraph")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    use_gemini = is_valid_key(api_key) and GEMINI_AVAILABLE

    if use_gemini:
        print("[Info] Running with real Google Gemini LLM calls!")
    else:
        print("[Info] Running fallback node (Set valid GEMINI_API_KEY in agent-playground/.env for real LLM calls).")

    builder = create_graph(use_gemini)
    graph = builder.compile(checkpointer=tracer.callback)

    print("\n>>> RECORD MODE <<<")
    start_time = time.time()
    with VCREngine(mode="record") as vcr:
        with tracer.trace("joke_session"):
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            result1 = graph.invoke({"messages": [HumanMessage(content="Tell me a funny programming joke.")]}, config)

    duration1 = time.time() - start_time

    print(f"Final State (Record): {result1['messages'][-1].content}")
    print(f"Record Duration: {duration1:.2f}s")

    cassettes = vcr.cassettes

    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode="replay")
    replay_vcr.load_cassettes(cassettes)
    
    start_time = time.time()
    with replay_vcr:
        with tracer.trace("joke_session"):
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            result2 = graph.invoke({"messages": [HumanMessage(content="Tell me a funny programming joke.")]}, config)

    duration2 = time.time() - start_time

    print(f"Final State (Replay): {result2['messages'][-1].content}")
    print(f"Replay Duration: {duration2:.2f}s")

    assert result1['messages'][-1].content == result2['messages'][-1].content
    print("\nSUCCESS: Graph replayed deterministically!")


if __name__ == "__main__":
    run_demo()
