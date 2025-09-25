import os
import sqlite3
from typing import Dict, List, Tuple


def open_db(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_float_data(conn: sqlite3.Connection, platform_number: str, limit: int = 200) -> List[Dict]:
    table = f"float_{platform_number}"
    cur = conn.execute(
        f"""
        SELECT profile_id, latitude, longitude, time, depth_min, depth_max,
               temperature_avg, salinity_avg, pressure_avg
        FROM {table}
        ORDER BY time DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(row) for row in cur.fetchall()]


def fetch_multiple(conn: sqlite3.Connection, platforms: List[str], per_float_limit: int = 200) -> Dict[str, List[Dict]]:
    out: Dict[str, List[Dict]] = {}
    for pid in platforms:
        try:
            out[pid] = fetch_float_data(conn, pid, per_float_limit)
        except Exception:
            out[pid] = []
    return out


