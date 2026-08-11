from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from chronos.core.schemas import AgentTrace, AgentSpan, CheckpointEvent
from chronos_server import db
from chronos_server import blob_storage
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import uuid
import logging
from datetime import datetime

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

# ── Health ────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.2.0"}

# ── Helpers ───────────────────────────────────────────────────────────

def fetch_dict(conn, query, params=None):
    cursor = conn.execute(query, params or [])
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# ── Ingestion Endpoints ──────────────────────────────────────────────

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
    input_blob_path = blob_storage.save_json_blob(span.inputs) if span.inputs else None
    output_blob_path = blob_storage.save_json_blob(span.outputs) if span.outputs else None

    # Extract token usage
    token_usage = span.token_usage or {}
    prompt_tokens = token_usage.get("prompt_tokens", token_usage.get("input_tokens", 0)) or 0
    completion_tokens = token_usage.get("completion_tokens", token_usage.get("output_tokens", 0)) or 0
    total_tokens = prompt_tokens + completion_tokens
    model = token_usage.get("model", "")

    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO spans (id, trace_id, parent_id, type, name, status, start_time, end_time, duration_ms, input_blob_path, output_blob_path, metadata, model, prompt_tokens, completion_tokens, total_tokens, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                end_time = EXCLUDED.end_time,
                duration_ms = EXCLUDED.duration_ms,
                output_blob_path = EXCLUDED.output_blob_path,
                metadata = EXCLUDED.metadata,
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                total_tokens = EXCLUDED.total_tokens,
                model = EXCLUDED.model
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
                json.dumps(token_usage) if token_usage else "{}",
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                0.0,  # cost placeholder
            ]
        )
        # Update trace aggregate tokens
        if total_tokens > 0:
            conn.execute(
                "UPDATE traces SET total_tokens = COALESCE(total_tokens, 0) + ? WHERE id = ?",
                [total_tokens, str(span.trace_id)]
            )
    finally:
        conn.close()
    return {"status": "success"}

@app.post("/api/checkpoints")
def ingest_checkpoint(checkpoint: CheckpointEvent):
    if checkpoint.is_binary:
        blob_path = blob_storage.save_binary_blob(bytes.fromhex(checkpoint.state_blob))
    else:
        blob_path = blob_storage.save_json_blob(json.loads(checkpoint.state_blob))
        
    conn = db.get_connection()
    try:
        # Calculate step_index for this trace
        step_count = conn.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE trace_id = ?", 
            [str(checkpoint.trace_id)]
        ).fetchone()[0]
        
        conn.execute(
            """
            INSERT INTO checkpoints (id, trace_id, span_id, name, timestamp, blob_path, is_binary, step_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                str(checkpoint.id),
                str(checkpoint.trace_id),
                str(checkpoint.span_id),
                checkpoint.name,
                checkpoint.timestamp,
                blob_path,
                checkpoint.is_binary,
                step_count,
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

# ── Query Endpoints ──────────────────────────────────────────────────

@app.delete("/api/traces")
def delete_all_traces():
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM spans")
        conn.execute("DELETE FROM checkpoints")
        conn.execute("DELETE FROM traces")
    finally:
        conn.close()
    return {"status": "success"}

class DeleteTracesRequest(BaseModel):
    ids: List[str]

@app.delete("/api/traces/batch")
def delete_selected_traces(req: DeleteTracesRequest):
    if not req.ids:
        return {"status": "success"}
    conn = db.get_connection()
    try:
        placeholders = ",".join(["?"] * len(req.ids))
        conn.execute(f"DELETE FROM spans WHERE trace_id IN ({placeholders})", req.ids)
        conn.execute(f"DELETE FROM checkpoints WHERE trace_id IN ({placeholders})", req.ids)
        conn.execute(f"DELETE FROM traces WHERE id IN ({placeholders})", req.ids)
    finally:
        conn.close()
    return {"status": "success"}

@app.get("/api/traces")
def get_traces(
    status: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    is_golden: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100),
):
    conn = db.get_connection()
    try:
        query = "SELECT * FROM traces WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if project:
            query += " AND project ILIKE ?"
            params.append(f"%{project}%")
        if is_golden is not None:
            query += " AND is_golden = ?"
            params.append(is_golden)
        if search:
            query += " AND (id ILIKE ? OR project ILIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += f" ORDER BY start_time DESC LIMIT {limit}"
        return fetch_dict(conn, query, params)
    finally:
        conn.close()

@app.get("/api/traces/{trace_id}")
def get_trace(trace_id: str):
    conn = db.get_connection()
    try:
        res = fetch_dict(conn, "SELECT * FROM traces WHERE id = ?", [trace_id])
        if not res:
            raise HTTPException(status_code=404, detail="Trace not found")
        return res[0]
    finally:
        conn.close()

@app.get("/api/traces/{trace_id}/spans")
def get_trace_spans(trace_id: str):
    conn = db.get_connection()
    try:
        spans = fetch_dict(conn, "SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time ASC", [trace_id])
        for span in spans:
            if span.get('input_blob_path'):
                span['inputs'] = blob_storage.load_json_blob(span['input_blob_path'])
            if span.get('output_blob_path'):
                span['outputs'] = blob_storage.load_json_blob(span['output_blob_path'])
        return spans
    finally:
        conn.close()

@app.get("/api/traces/{trace_id}/checkpoints")
def get_trace_checkpoints(trace_id: str):
    conn = db.get_connection()
    try:
        checkpoints = fetch_dict(conn, "SELECT * FROM checkpoints WHERE trace_id = ? ORDER BY timestamp ASC", [trace_id])
        for cp in checkpoints:
            if not cp['is_binary'] and cp.get('blob_path'):
                cp['state'] = blob_storage.load_json_blob(cp['blob_path'])
        return checkpoints
    finally:
        conn.close()

# ── Stats / Analytics ────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    conn = db.get_connection()
    try:
        traces_count = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        success_count = conn.execute("SELECT COUNT(*) FROM traces WHERE status = 'success'").fetchone()[0]
        error_count = conn.execute("SELECT COUNT(*) FROM traces WHERE status = 'error'").fetchone()[0]
        total_tokens = conn.execute("SELECT COALESCE(SUM(total_tokens), 0) FROM spans").fetchone()[0]
        total_spans = conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0]
        avg_duration = conn.execute("SELECT COALESCE(AVG(duration_ms), 0) FROM spans WHERE duration_ms > 0").fetchone()[0]
        
        # Token usage by model
        model_usage = fetch_dict(conn, """
            SELECT model, SUM(prompt_tokens) as prompt_tokens, SUM(completion_tokens) as completion_tokens, 
                   SUM(total_tokens) as total_tokens, COUNT(*) as calls
            FROM spans WHERE model IS NOT NULL AND model != '' GROUP BY model
        """)
        
        # Activity over time (last 24h, grouped by hour)
        activity = fetch_dict(conn, """
            SELECT DATE_TRUNC('hour', start_time) as hour, COUNT(*) as count, 
                   SUM(COALESCE(total_tokens, 0)) as tokens
            FROM traces WHERE start_time > CURRENT_TIMESTAMP - INTERVAL '24 HOURS'
            GROUP BY DATE_TRUNC('hour', start_time) ORDER BY hour
        """)
        
        return {
            "traces_count": traces_count,
            "success_count": success_count,
            "error_count": error_count,
            "total_tokens": total_tokens,
            "total_spans": total_spans,
            "avg_duration_ms": round(avg_duration, 2),
            "model_usage": model_usage,
            "activity": activity,
        }
    finally:
        conn.close()

# ── Evaluations ──────────────────────────────────────────────────────

class EvaluationCreate(BaseModel):
    trace_id: str
    name: str
    score: float
    label: Optional[str] = None
    comment: Optional[str] = None
    method: str = "manual"

@app.post("/api/evaluations")
def create_evaluation(ev: EvaluationCreate):
    conn = db.get_connection()
    try:
        eval_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO evaluations (id, trace_id, name, score, label, comment, method) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [eval_id, ev.trace_id, ev.name, ev.score, ev.label, ev.comment, ev.method]
        )
        return {"id": eval_id, "status": "success"}
    finally:
        conn.close()

@app.get("/api/evaluations")
def get_evaluations(trace_id: Optional[str] = Query(None)):
    conn = db.get_connection()
    try:
        if trace_id:
            return fetch_dict(conn, "SELECT * FROM evaluations WHERE trace_id = ? ORDER BY created_at DESC", [trace_id])
        return fetch_dict(conn, "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT 100")
    finally:
        conn.close()

# ── Annotations (Human Feedback) ────────────────────────────────────

class AnnotationCreate(BaseModel):
    trace_id: str
    span_id: Optional[str] = None
    rating: int  # 1-5 or thumbs -1/1
    label: Optional[str] = None
    comment: Optional[str] = None
    author: str = "anonymous"

@app.post("/api/annotations")
def create_annotation(ann: AnnotationCreate):
    conn = db.get_connection()
    try:
        ann_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO annotations (id, trace_id, span_id, rating, label, comment, author) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [ann_id, ann.trace_id, ann.span_id, ann.rating, ann.label, ann.comment, ann.author]
        )
        return {"id": ann_id, "status": "success"}
    finally:
        conn.close()

@app.get("/api/annotations")
def get_annotations(trace_id: Optional[str] = Query(None)):
    conn = db.get_connection()
    try:
        if trace_id:
            return fetch_dict(conn, "SELECT * FROM annotations WHERE trace_id = ? ORDER BY created_at DESC", [trace_id])
        return fetch_dict(conn, "SELECT * FROM annotations ORDER BY created_at DESC LIMIT 100")
    finally:
        conn.close()

# ── Golden Traces & Regression ───────────────────────────────────────

@app.post("/api/traces/{trace_id}/pin")
def pin_golden_trace(trace_id: str):
    conn = db.get_connection()
    try:
        conn.execute("UPDATE traces SET is_golden = TRUE WHERE id = ?", [trace_id])
        return {"status": "pinned"}
    finally:
        conn.close()

@app.post("/api/traces/{trace_id}/unpin")
def unpin_golden_trace(trace_id: str):
    conn = db.get_connection()
    try:
        conn.execute("UPDATE traces SET is_golden = FALSE WHERE id = ?", [trace_id])
        return {"status": "unpinned"}
    finally:
        conn.close()

@app.get("/api/golden")
def get_golden_traces():
    conn = db.get_connection()
    try:
        return fetch_dict(conn, "SELECT * FROM traces WHERE is_golden = TRUE ORDER BY start_time DESC")
    finally:
        conn.close()
