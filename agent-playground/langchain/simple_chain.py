import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

from langchain_core.prompts import PromptTemplate
from chronos import Chronos
from chronos.interceptors.vcr import VCREngine, VCRMode

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and not key.startswith("YOUR_"))


def run_demo():
    print("--- LangChain + Chronos Integration Test ---")

    tracer = Chronos("LangchainBot", framework="langchain")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not is_valid_key(api_key) or not GEMINI_AVAILABLE:
        print("\n[!] No valid GEMINI_API_KEY found.")
        print("Please replace 'YOUR_GEMINI_API_KEY' in agent-playground/.env with your actual key from https://aistudio.google.com/")
        print("Adapter and callback system initialized successfully!")
        return

    # Real Gemini model call
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0, callbacks=[tracer.callback])
    prompt = PromptTemplate.from_template("What is the capital of {country}? Answer in one short sentence.")
    chain = prompt | llm

    print("\n>>> RECORD MODE <<<")
    with VCREngine(mode="record") as vcr:
        with tracer.trace("langchain_session"):
            result = chain.invoke({"country": "France"}, config={"callbacks": [tracer.callback]})
            print(f"Result (Record): {result.content}")

    cassettes = vcr.cassettes

    print("\n>>> REPLAY MODE <<<")
    replay_vcr = VCREngine(mode="replay")
    replay_vcr.load_cassettes(cassettes)
    
    with replay_vcr:
        with tracer.trace("langchain_session"):
            result2 = chain.invoke({"country": "France"}, config={"callbacks": [tracer.callback]})
            print(f"Result (Replay): {result2.content}")
    assert result.content == result2.content
    print("\nSUCCESS: LangChain + Gemini natively traced (LLM & Chain Start/End callbacks triggered)!")


if __name__ == "__main__":
    run_demo()
