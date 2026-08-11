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
            metadata JSON,
            total_tokens INTEGER DEFAULT 0,
            total_cost DOUBLE DEFAULT 0.0,
            is_golden BOOLEAN DEFAULT FALSE,
            tags JSON DEFAULT '[]'
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
            metadata JSON,
            model VARCHAR,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost DOUBLE DEFAULT 0.0
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
            is_binary BOOLEAN,
            step_index INTEGER DEFAULT 0
        )
    """)
    
    # Evaluations Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id VARCHAR PRIMARY KEY,
            trace_id VARCHAR,
            name VARCHAR,
            score DOUBLE,
            label VARCHAR,
            comment TEXT,
            method VARCHAR DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSON DEFAULT '{}'
        )
    """)
    
    # Annotations Table (human feedback)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            id VARCHAR PRIMARY KEY,
            trace_id VARCHAR,
            span_id VARCHAR,
            rating INTEGER,
            label VARCHAR,
            comment TEXT,
            author VARCHAR DEFAULT 'anonymous',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Try to add new columns to existing tables (idempotent migration)
    _safe_add_columns(conn)
    
    return conn

def _safe_add_columns(conn):
    """Safely add new columns to existing tables without failing."""
    migrations = [
        ("traces", "total_tokens", "INTEGER DEFAULT 0"),
        ("traces", "total_cost", "DOUBLE DEFAULT 0.0"),
        ("traces", "is_golden", "BOOLEAN DEFAULT FALSE"),
        ("traces", "tags", "JSON DEFAULT '[]'"),
        ("spans", "model", "VARCHAR"),
        ("spans", "prompt_tokens", "INTEGER DEFAULT 0"),
        ("spans", "completion_tokens", "INTEGER DEFAULT 0"),
        ("spans", "total_tokens", "INTEGER DEFAULT 0"),
        ("spans", "cost", "DOUBLE DEFAULT 0.0"),
        ("checkpoints", "step_index", "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass  # Column already exists

def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))
