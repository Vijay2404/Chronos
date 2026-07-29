from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent
from chronos_server import db
from chronos_server import blob_storage
from typing import Dict, Any, List
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chronos_server")

app = FastAPI(title="Chronos Local Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    logger.info("Initializing DuckDB...")
    db.init_db()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/api/traces")
def ingest_trace(trace: AgentTrace):
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO traces (id, project, status, start_time, end_time, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                end_time = EXCLUDED.end_time,
                metadata = EXCLUDED.metadata
            """,
            [
                str(trace.trace_id),
                trace.name,
                trace.status,
                trace.start_time,
                trace.end_time,
                json.dumps(trace.metadata)
            ]
        )
    finally:
        conn.close()
    return {"status": "success"}

@app.post("/api/spans")
def ingest_span(span: AgentSpan):
    # Save massive inputs/outputs as blobs to avoid DuckDB bloat
    input_blob_path = blob_storage.save_json_blob(span.inputs) if span.inputs else None
    output_blob_path = blob_storage.save_json_blob(span.outputs) if span.outputs else None

    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO spans (id, trace_id, parent_id, type, name, status, start_time, end_time, duration_ms, input_blob_path, output_blob_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                end_time = EXCLUDED.end_time,
                duration_ms = EXCLUDED.duration_ms,
                output_blob_path = EXCLUDED.output_blob_path,
                metadata = EXCLUDED.metadata
            """,
            [
                str(span.span_id),
                str(span.trace_id),
                str(span.parent_span_id) if span.parent_span_id else None,
                span.span_type,
                span.name,
                span.status,
                span.timestamp,
                span.end_timestamp,
                span.duration_ms,
                input_blob_path,
                output_blob_path,
                json.dumps(span.token_usage) if span.token_usage else "{}"
            ]
        )
    finally:
        conn.close()
    return {"status": "success"}

@app.post("/api/checkpoints")
def ingest_checkpoint(checkpoint: CheckpointEvent):
    if checkpoint.is_binary:
        # It's a hex encoded binary string
        blob_path = blob_storage.save_binary_blob(bytes.fromhex(checkpoint.state_blob))
    else:
        # It's a json string
        blob_path = blob_storage.save_json_blob(json.loads(checkpoint.state_blob))
        
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO checkpoints (id, trace_id, span_id, name, timestamp, blob_path, is_binary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                str(checkpoint.id),
                str(checkpoint.trace_id),
                str(checkpoint.span_id),
                checkpoint.name,
                checkpoint.timestamp,
                blob_path,
                checkpoint.is_binary
            ]
        )
    finally:
        conn.close()
    return {"status": "success"}

@app.post("/api/cassettes")
async def ingest_cassette(request: Request):
    """Save a VCR cassette dict."""
    cassette = await request.json()
    request_hash = cassette.get("hash")
    if not request_hash:
        raise HTTPException(status_code=400, detail="Missing hash in cassette")
        
    blob_path = blob_storage.save_json_blob(cassette)
    
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO cassettes (id, request_hash, blob_path, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
            """,
            [str(uuid.uuid4()) if "id" not in cassette else cassette["id"], request_hash, blob_path]
        )
    except Exception as e:
        logger.warning(f"Failed to insert cassette to db: {e}")
    finally:
        conn.close()
        
    return {"status": "success"}

@app.get("/api/cassettes/{request_hash}")
def get_cassette(request_hash: str):
    conn = db.get_connection()
    try:
        result = conn.execute("SELECT blob_path FROM cassettes WHERE request_hash = ? ORDER BY created_at DESC LIMIT 1", [request_hash]).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Cassette not found")
            
        blob_path = result[0]
        data = blob_storage.load_json_blob(blob_path)
        if not data:
            raise HTTPException(status_code=404, detail="Blob data missing")
            
        return data
    finally:
        conn.close()
