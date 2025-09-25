import sqlite3
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def _db_path() -> str:
    return str(Path("data") / "argo.db")

def execute_sql_query(query):
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        return results
    finally:
        conn.close()


def fetch_latest_for_platforms_sqlite(platform_ids, limit=20):
    """Fetch latest records across per-float tables by UNION ALL.

    Skips platform IDs whose tables are missing.
    Returns list of rows as tuples.
    """
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.cursor()
        parts = []
        for pid in platform_ids or []:
            table = f"float_{pid}"
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cur.fetchone() is None:
                continue
            parts.append(
                f"SELECT profile_id, latitude, longitude, time, "
                f"temperature_avg, salinity_avg, depth_min, depth_max, '{pid}' AS platform_number "
                f"FROM {table} WHERE temperature_avg IS NOT NULL AND salinity_avg IS NOT NULL"
            )
        if not parts:
            return []
        union_sql = "\nUNION ALL\n".join(parts) + "\nORDER BY time DESC\nLIMIT ?"
        cur.execute(union_sql, (int(limit),))
        return cur.fetchall()
    finally:
        conn.close()

def query_vector_db(collection, query_text, n_results=5):
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results