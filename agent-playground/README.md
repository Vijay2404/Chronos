# Chronos Agent Playground

This is the sandbox environment for testing the `chronos-sdk` against real-world agent frameworks before full integration.

## Available Sandboxes

- `raw_python/`: Testing raw HTTP requests, basic functions, and Chronos VCR interception.
- `langgraph/`: (Coming Soon) Testing the LangGraph callback handler.
- `crewai/`: (Coming Soon) Testing CrewAI integration.

## Usage

```bash
# Run raw python example
uv run python raw_python/weather_agent.py
```
