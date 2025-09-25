import os

from scripts.rebuild_argo_sqlite import open_db, list_platforms_from_csv, discover_csv_for_float, upsert_from_csv, create_float_table


def main() -> None:
    db_path = os.path.join("data", "argo.db")
    csv_dir = os.path.join("data", "csv")

    conn = open_db(db_path)
    try:
        platforms = list_platforms_from_csv(csv_dir)
        for pid in platforms:
            create_float_table(conn, pid)
        total_rows = 0
        for pid in platforms:
            path = discover_csv_for_float(csv_dir, pid)
            if path:
                total_rows += upsert_from_csv(conn, pid, path)
        conn.commit()
        print(f"SQLite complete. Upserted {total_rows} rows across {len(platforms)} floats. DB: {db_path}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()


