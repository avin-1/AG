import sqlite3

# Configure these
db_path = "data/argo.db"
platform_numbers = ["1901898", "6903058", "2902768"]
limit = 20

conn = sqlite3.connect(db_path)
try:
    cur = conn.cursor()
    parts = []
    used = []
    skipped = []
    for pid in platform_numbers:
        table = f"float_{pid}"
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cur.fetchone() is None:
            skipped.append(pid)
            continue
        used.append(pid)
        parts.append(
            f"SELECT profile_id, latitude, longitude, time, "
            f"temperature_avg, salinity_avg, depth_min, depth_max, '{pid}' AS platform_number "
            f"FROM {table} "
            f"WHERE temperature_avg IS NOT NULL AND salinity_avg IS NOT NULL"
        )

    if not parts:
        print("No matching float tables exist for:", platform_numbers)
    else:
        union_sql = "\nUNION ALL\n".join(parts)
        final_sql = union_sql + "\nORDER BY time DESC\nLIMIT ?"
        cur.execute(final_sql, (limit,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        print("Using platforms:", used)
        if skipped:
            print("Skipped (no table):", skipped)
        print("Columns:", columns)
        for row in rows:
            print(row)
finally:
    conn.close()