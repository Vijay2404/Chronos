import os
import uuid
import time
import logging
import json
from pathlib import Path
from typing import TypedDict, Annotated, Literal
import operator
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="ComplexReActAgent")

# 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BINDING)
from chronos.adapters.langgraph import ChronosCheckpointer
from langchain_google_genai import ChatGoogleGenerativeAI


# --- Define Tools ---

@tool
def get_weather(location: str) -> str:
    """Returns the current weather for a given location."""
    print(f"[Tool] get_weather called for {location}")
    # Mocking some weather data
    if "san francisco" in location.lower() or "sf" in location.lower():
        return "It's 65°F and foggy."
    elif "new york" in location.lower() or "ny" in location.lower():
        return "It's 80°F and sunny."
    return f"Weather data not found for {location}."

@tool
def calculate_math(expression: str) -> str:
    """Evaluates a simple math expression like '123 * 456'."""
    print(f"[Tool] calculate_math called for {expression}")
    try:
        # Extremely unsafe eval for demo purposes!
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating math: {str(e)}"

tools = [get_weather, calculate_math]


# --- Define State and Graph ---

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

def create_react_graph():
    builder = StateGraph(AgentState)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        print("[Node] agent_node invoking LLM...")
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def tools_node(state: AgentState):
        print("[Node] tools_node executing tools...")
        last_message = state["messages"][-1]
        
        tool_responses = []
        # LLM requested tool calls
        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                # Find the tool by name
                tool_func = next((t for t in tools if t.name == tool_call["name"]), None)
                if tool_func:
                    result = tool_func.invoke(tool_call["args"])
                    tool_responses.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call["id"], name=tool_call["name"])
                    )
        
        return {"messages": tool_responses}

    def should_continue(state: AgentState) -> Literal["tools_node", "END"]:
        last_message = state["messages"][-1]
        # If there is no function call, then we finish
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            print("[Edge] should_continue -> END")
            return "END"
        # Otherwise if there is, we continue
        print("[Edge] should_continue -> tools_node")
        return "tools_node"

    builder.add_node("agent_node", agent_node)
    builder.add_node("tools_node", tools_node)

    # Define edges: START -> agent -> conditional -> tool -> agent
    builder.add_edge(START, "agent_node")
    builder.add_conditional_edges("agent_node", should_continue, {"tools_node": "tools_node", "END": END})
    builder.add_edge("tools_node", "agent_node")

    return builder


def run_demo():
    print("--- LangGraph ReAct Agent + Chronos ---")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("[Error] GOOGLE_API_KEY is not set. Please set it in agent-playground/.env")
        return

    builder = create_react_graph()
    
    # Passing ChronosCheckpointer automatically traces all nodes!
    graph = builder.compile(checkpointer=ChronosCheckpointer())

    start_time = time.time()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # Complex prompt that requires both tools to be used
    prompt = "What's the weather in San Francisco? Also, what is 123 multiplied by 456? Please answer both clearly."
    print(f"\n[Input] {prompt}\n")
    
    result = graph.invoke({"messages": [HumanMessage(content=prompt)]}, config)

    duration = time.time() - start_time

    print(f"\n[Final Output]: {result['messages'][-1].content}")
    print(f"Duration: {duration:.2f}s")
    print("\n[i] Open Chronos UI to see the execution graph and state diffing!")

if __name__ == "__main__":
    run_demo()
