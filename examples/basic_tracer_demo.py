import time
from chronos import Chronos

def main():
    chronos = Chronos(agent_name="WeatherAssistantAgent")

    # Start trace using context manager
    with chronos.trace(name="get_weather_flow"):

        # Step 1: Reason about the request
        with chronos.step(name="plan_action", step_type="reasoning", inputs={"user_prompt": "What's the weather in Tokyo?"}):
            time.sleep(0.1)
            # Checkpoint initial memory (JSON serializable)
            chronos.checkpoint(state={"memory": ["user asked for weather in Tokyo"], "step": 1})

        # Step 2: Execute tool call
        with chronos.step(name="fetch_weather_api", step_type="tool", inputs={"location": "Tokyo"}):
            time.sleep(0.2)
            api_result = {"temperature": "22C", "condition": "Sunny"}
            
            # Complex non-JSON object checkpoint (demonstrating hybrid fallback)
            class CustomConnection:
                def __init__(self):
                    self.conn_str = "db://live_connection"
            
            chronos.snapshot(
                state={"memory": ["fetched Tokyo weather"], "active_connection": CustomConnection()},
                name="post_tool_checkpoint"
            )
    
    print("\n--- Execution Summary ---")
    print(f"Captured Events ({len(chronos.events)} total):")
    for ev in chronos.events:
        print(f" - [{ev.__class__.__name__}] {ev.name}")

if __name__ == "__main__":
    main()
