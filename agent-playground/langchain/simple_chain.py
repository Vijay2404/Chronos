"""
LangChain + Chronos Integration Test (New DX)
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

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from langchain_core.prompts import PromptTemplate

# 1. 🛑 THE HORIZONTAL BAR (MAGIC INIT)
import chronos
chronos.init(project="LangchainBot")

from chronos.adapters.langchain import ChronosLangchainCallback

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


def run_demo():
    print("--- LangChain + Chronos Integration Test ---")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not is_valid_key(api_key) or not GEMINI_AVAILABLE:
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")
        return

    # Real Gemini model call
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    prompt = PromptTemplate.from_template("What is the capital of {country}? Answer in one short sentence.")
    chain = prompt | llm

    # 2. ⬇️ THE VERTICAL DEPTH (EXPLICIT BINDING)
    # The tracer callback auto-starts a trace and records everything
    start_time = time.time()
    
    result = chain.invoke(
        {"country": "France"}, 
        config={"callbacks": [ChronosLangchainCallback()]}
    )
    
    duration = time.time() - start_time
    
    print(f"\nResult: {result.content}")
    print(f"Duration: {duration:.2f}s")
    print("\nSUCCESS: LangChain natively traced!")
    print("[i] Run this with `CHRONOS_REPLAY_MODE=1 python simple_chain.py` to test Replay Mode!")


if __name__ == "__main__":
    run_demo()
