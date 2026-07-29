import duckdb

def main():
    print("Opening DuckDB Database at .chronos/chronos.duckdb...\n")
    conn = duckdb.connect(".chronos/chronos.duckdb")
    
    print("=== TRACES ===")
    traces = conn.execute("SELECT id, project, status, start_time FROM traces").fetchall()
    for row in traces:
        print(row)
        
    print("\n=== CHECKPOINTS ===")
    checkpoints = conn.execute("SELECT id, name, is_binary FROM checkpoints").fetchall()
    for row in checkpoints:
        print(row)
        
    print("\n=== CASSETTES (VCR Caches) ===")
    cassettes = conn.execute("SELECT request_hash, blob_path FROM cassettes").fetchall()
    for row in cassettes:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    main()
