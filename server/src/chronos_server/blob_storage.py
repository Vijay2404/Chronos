import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Union

BLOB_DIR = Path(".chronos") / "blobs"

def _ensure_dir():
    os.makedirs(BLOB_DIR, exist_ok=True)

def save_json_blob(data: Union[Dict[str, Any], list]) -> str:
    """Save a JSON serializable dict/list to blob storage and return the path."""
    _ensure_dir()
    blob_id = str(uuid.uuid4())
    path = BLOB_DIR / f"{blob_id}.json"
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    return str(path)

def load_json_blob(path: str) -> Union[Dict[str, Any], list, None]:
    """Load JSON from a blob path."""
    p = Path(path)
    if not p.exists():
        return None
        
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_binary_blob(data: bytes) -> str:
    """Save raw binary (e.g., cloudpickle) to blob storage and return path."""
    _ensure_dir()
    blob_id = str(uuid.uuid4())
    path = BLOB_DIR / f"{blob_id}.bin"
    
    with open(path, "wb") as f:
        f.write(data)
        
    return str(path)
