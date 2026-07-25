import json
from pathlib import Path
from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent, AgentEvent

def export():
    # sdk/python/scripts -> sdk/schemas
    output_dir = Path(__file__).parents[2] / "schemas"
    output_dir.mkdir(exist_ok=True)
    
    models = {
        "agent_event.json": AgentEvent,
        "agent_trace.json": AgentTrace,
        "agent_span.json": AgentSpan,
        "checkpoint_event.json": CheckpointEvent
    }
    
    for filename, model in models.items():
        filepath = output_dir / filename
        schema = model.model_json_schema()
        filepath.write_text(json.dumps(schema, indent=2))
        print(f"Exported JSON Schema: {filepath}")

if __name__ == "__main__":
    export()
