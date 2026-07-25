import os
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from chronos.core.tracer import Chronos
from chronos.adapters.langchain import ChronosLangchainCallback
from chronos.interceptors.vcr import VCREngine, VCRMode

def run_demo():
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "dummy-key")
    
    chronos = Chronos(agent_name="LangchainBot")
    callback = ChronosLangchainCallback(chronos)
    
    # Initialize LLM with the callback!
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, callbacks=[callback])
    
    prompt = PromptTemplate.from_template("What is the capital of {country}?")
    chain = prompt | llm
    
    trace_id = uuid.uuid4()
    
    print("--- LangChain + Chronos Integration Test ---")
    
    if os.getenv("OPENAI_API_KEY") != "dummy-key":
        print("\n>>> RECORD MODE <<<")
        vcr = VCREngine(mode=VCRMode.RECORD)
        vcr.enable()
        
        with chronos.trace("langchain_session", force_trace_id=trace_id):
            result = chain.invoke({"country": "France"}, config={"callbacks": [callback]})
            print(result.content)
            
        vcr.disable()
        cassettes = vcr.cassettes
        
        print("\n>>> REPLAY MODE <<<")
        replay_vcr = VCREngine(mode=VCRMode.REPLAY)
        replay_vcr.load_cassettes(cassettes)
        replay_vcr.enable()
        
        with chronos.trace("langchain_session", force_trace_id=trace_id):
            result2 = chain.invoke({"country": "France"}, config={"callbacks": [callback]})
            print(result2.content)
            
        replay_vcr.disable()
        assert result.content == result2.content
        print("SUCCESS: LangChain natively traced and replayed!")
    else:
        print("Set OPENAI_API_KEY to run the full integration. Adapter loaded!")

if __name__ == "__main__":
    run_demo()
