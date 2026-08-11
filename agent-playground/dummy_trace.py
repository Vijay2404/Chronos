import time
import chronos

chronos.init(project="Dummy-Mock-Agent")
tracer = chronos.get_tracer()

print("Generating dummy trace with spans...")
with tracer.trace("dummy_react_flow"):
    # Span 1: agent_node
    with tracer.step("agent_node", inputs={"messages": [{"role": "user", "content": "What's the weather in SF?"}]}) as span1:
        time.sleep(0.5)
        span1.outputs = {"tool_calls": [{"name": "get_weather", "args": {"location": "SF"}}]}
    tracer.checkpoint(name="after_agent", state={"messages": [{"role": "user", "content": "What's the weather in SF?"}, {"role": "assistant", "tool_calls": [{"name": "get_weather", "args": {"location": "SF"}}]}]})

    # Span 2: tools_node
    with tracer.step("tools_node", inputs={"tool_calls": [{"name": "get_weather", "args": {"location": "SF"}}]}) as span2:
        time.sleep(0.3)
        span2.outputs = {"messages": [{"role": "tool", "content": "65F and foggy"}]}
    tracer.checkpoint(name="after_tools", state={"messages": [{"role": "user", "content": "What's the weather in SF?"}, {"role": "assistant", "tool_calls": [{"name": "get_weather", "args": {"location": "SF"}}]}, {"role": "tool", "content": "65F and foggy"}]})

    # Span 3: agent_node (loop back)
    with tracer.step("agent_node", inputs={"messages": [{"role": "tool", "content": "65F and foggy"}]}) as span3:
        time.sleep(0.6)
        span3.outputs = {"messages": [{"role": "assistant", "content": "It is 65F and foggy in SF."}]}
    tracer.checkpoint(name="final_answer", state={"messages": [{"role": "user", "content": "What's the weather in SF?"}, {"role": "assistant", "tool_calls": [{"name": "get_weather", "args": {"location": "SF"}}]}, {"role": "tool", "content": "65F and foggy"}, {"role": "assistant", "content": "It is 65F and foggy in SF."}]})

print("Done!")
