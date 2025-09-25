import argparse
import csv
import os
import sqlite3
from datetime import datetime
from typing import Iterable, List, Mapping, Optional


def open_db(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _table_name(platform_number: str) -> str:
    return f"float_{platform_number}"


def create_float_table(conn: sqlite3.Connection, platform_number: str) -> None:
    table = _table_name(platform_number)
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            latitude REAL,
            longitude REAL,
            time TEXT,
            depth_min REAL,
            depth_max REAL,
            temperature_avg REAL,
            salinity_avg REAL,
            pressure_avg REAL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE (profile_id, time)
        )
        """
    )
    conn.execute(f"CREATE INDEX IF NOT EXISTS {table}_time_desc_idx ON {table} (time DESC)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS {table}_profile_id_idx ON {table} (profile_id)")


def _to_float(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return None


def _normalize_time(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip().replace("T", " ").replace("Z", "")
        # try a few common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    return None


def upsert_float_records(
    conn: sqlite3.Connection,
    platform_number: str,
    records: Iterable[Mapping[str, object]],
) -> int:
    create_float_table(conn, platform_number)
    table = _table_name(platform_number)

    rows: List[tuple] = []
    for rec in records:
        rows.append(
            (
                rec.get("profile_id"),
                _to_float(rec.get("latitude")),
                _to_float(rec.get("longitude")),
                _normalize_time(rec.get("time")),
                _to_float(rec.get("depth_min")),
                _to_float(rec.get("depth_max")),
                _to_float(rec.get("temperature_avg")),
                _to_float(rec.get("salinity_avg")),
                _to_float(rec.get("pressure_avg")),
            )
        )

    if not rows:
        return 0

    conn.executemany(
        f"""
        INSERT INTO {table} (
            profile_id, latitude, longitude, time,
            depth_min, depth_max,
            temperature_avg, salinity_avg, pressure_avg
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(profile_id, time) DO UPDATE SET
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            depth_min=excluded.depth_min,
            depth_max=excluded.depth_max,
            temperature_avg=excluded.temperature_avg,
            salinity_avg=excluded.salinity_avg,
            pressure_avg=excluded.pressure_avg
        """,
        rows,
    )
    return len(rows)


def upsert_from_csv(conn: sqlite3.Connection, platform_number: str, csv_path: str) -> int:
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        normalized = []
        for row in reader:
            normalized.append(
                {
                    "profile_id": row.get("profile_id") or row.get("PROFILE_ID") or row.get("profile"),
                    "latitude": row.get("latitude") or row.get("LATITUDE") or row.get("lat"),
                    "longitude": row.get("longitude") or row.get("LONGITUDE") or row.get("lon"),
                    "time": row.get("time") or row.get("TIME") or row.get("date"),
                    "depth_min": row.get("depth_min") or row.get("DEPTH_MIN") or row.get("z_min"),
                    "depth_max": row.get("depth_max") or row.get("DEPTH_MAX") or row.get("z_max"),
                    "temperature_avg": row.get("temperature_avg") or row.get("TEMP_AVG") or row.get("temperature"),
                    "salinity_avg": row.get("salinity_avg") or row.get("SALINITY_AVG") or row.get("salinity"),
                    "pressure_avg": row.get("pressure_avg") or row.get("PRESSURE_AVG") or row.get("pressure"),
                }
            )
    return upsert_float_records(conn, platform_number, normalized)


def fetch_latest_records(conn: sqlite3.Connection, platform_number: str, limit: int = 20):
    table = _table_name(platform_number)
    cur = conn.execute(
        f"""
        SELECT id, profile_id, latitude, longitude, time, depth_min, depth_max,
               temperature_avg, salinity_avg, pressure_avg, created_at
        FROM {table}
        ORDER BY time DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def discover_csv_for_float(csv_dir: str, platform_number: str) -> Optional[str]:
    for name in (f"float_{platform_number}.csv", f"{platform_number}.csv", f"ARGO_{platform_number}.csv"):
        path = os.path.join(csv_dir, name)
        if os.path.isfile(path):
            return path
    return None


def list_platforms_from_csv(csv_dir: str) -> List[str]:
    platforms: set[str] = set()
    if not csv_dir or not os.path.isdir(csv_dir):
        return []
    for name in os.listdir(csv_dir):
        if not name.endswith(".csv"):
            continue
        pid: Optional[str] = None
        # float_<digits>.csv
        if name.startswith("float_") and name.endswith(".csv"):
            core = name[len("float_") : -len(".csv")]
            if core.isdigit():
                pid = core
        # ARGO_<digits>.csv
        if pid is None and name.startswith("ARGO_") and name.endswith(".csv"):
            core = name[len("ARGO_") : -len(".csv")]
            if core.isdigit():
                pid = core
        # <digits>.csv
        if pid is None:
            core = name[:-len(".csv")]
            if core.isdigit():
                pid = core
        if pid:
            platforms.add(pid)
    return sorted(platforms)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/ingest ARGO per-float data into SQLite.")
    parser.add_argument("--db-path", default=os.path.join("data", "argo.db"))
    parser.add_argument("--floats", nargs="*", help="Platform numbers to create/ingest")
    parser.add_argument("--csv-dir", default=os.path.join("data", "csv"), help="Directory with per-float CSVs (default: data/csv)")
    parser.add_argument("--csv", action="append", nargs=2, metavar=("PLATFORM", "PATH"), help="Explicit mapping: PLATFORM PATH")
    parser.add_argument("--latest", metavar="PLATFORM", help="Print latest 20 rows for PLATFORM and exit")
    args = parser.parse_args()

    conn = open_db(args.db_path)
    try:
        if args.latest:
            for rec in fetch_latest_records(conn, args.latest, 20):
                print(rec)
            return

        float_list: List[str] = args.floats or []
        if args.csv:
            for platform_number, _ in args.csv:
                if platform_number not in float_list:
                    float_list.append(platform_number)

        # If user provided a CSV directory but no floats, auto-discover platforms from filenames
        if args.csv_dir and not float_list:
            float_list = list_platforms_from_csv(args.csv_dir)

        for platform_number in float_list:
            create_float_table(conn, platform_number)

        total_rows = 0
        if args.csv:
            for platform_number, path in args.csv:
                total_rows += upsert_from_csv(conn, platform_number, path)

        if args.csv_dir and float_list:
            for platform_number in float_list:
                discovered = discover_csv_for_float(args.csv_dir, platform_number)
                if discovered:
                    total_rows += upsert_from_csv(conn, platform_number, discovered)

        conn.commit()
        print(f"SQLite complete. Upserted {total_rows} rows across {len(float_list)} floats. DB: {args.db_path}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()


