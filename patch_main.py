import os

file_path = "c:/Users/Menaa/Chronos/Chronos/server/src/chronos_server/main.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoints = """

def fetch_dict(conn, query, params=None):
    cursor = conn.execute(query, params or [])
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

@app.get("/api/traces")
def get_traces():
    conn = db.get_connection()
    try:
        return fetch_dict(conn, "SELECT * FROM traces ORDER BY start_time DESC")
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
        # We don't load binary blobs into JSON response, only metadata
        for cp in checkpoints:
            if not cp['is_binary'] and cp.get('blob_path'):
                cp['state'] = blob_storage.load_json_blob(cp['blob_path'])
        return checkpoints
    finally:
        conn.close()
"""

if "def get_traces" not in content:
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(new_endpoints)
    print("Successfully patched main.py")
else:
    print("Already patched")
