import duckdb
import os
from pathlib import Path
from typing import Dict, Any, List

DB_PATH = Path(".chronos") / "chronos.duckdb"

def init_db() -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB database and create tables if they don't exist."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Traces Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id VARCHAR PRIMARY KEY,
            project VARCHAR,
            status VARCHAR,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_ms DOUBLE,
            metadata JSON
        )
    """)
    
    # Spans Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spans (
            id VARCHAR PRIMARY KEY,
            trace_id VARCHAR,
            parent_id VARCHAR,
            type VARCHAR,
            name VARCHAR,
            status VARCHAR,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_ms DOUBLE,
            input_blob_path VARCHAR,
            output_blob_path VARCHAR,
            metadata JSON
        )
    """)
    
    # Cassettes Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cassettes (
            id VARCHAR PRIMARY KEY,
            request_hash VARCHAR,
            blob_path VARCHAR,
            created_at TIMESTAMP,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            cost DOUBLE
        )
    """)
    
    # Checkpoints Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id VARCHAR PRIMARY KEY,
            trace_id VARCHAR,
            span_id VARCHAR,
            name VARCHAR,
            timestamp TIMESTAMP,
            blob_path VARCHAR,
            is_binary BOOLEAN
        )
    """)
    
    return conn

def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))
