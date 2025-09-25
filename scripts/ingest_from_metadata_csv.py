import argparse
import os
import sys
from pathlib import Path
import pandas as pd

# Allow running as: `python scripts/ingest_from_metadata_csv.py` or `python -m scripts.ingest_from_metadata_csv`
try:
    from scripts.nc_to_sqlite import parse_file
    from scripts.rebuild_argo_sqlite import open_db, upsert_float_records
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    try:
        from scripts.nc_to_sqlite import parse_file
        from scripts.rebuild_argo_sqlite import open_db, upsert_float_records
    except ModuleNotFoundError:
        from nc_to_sqlite import parse_file
        from rebuild_argo_sqlite import open_db, upsert_float_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest floats listed in metadata.csv into SQLite (from CSVs if available, else local argo_data .nc)")
    parser.add_argument("--metadata-csv", default=os.path.join("data", "processed", "metadata.csv"))
    parser.add_argument("--argo-dir", default="argo_data")
    parser.add_argument("--db-path", default=os.path.join("data", "argo.db"))
    parser.add_argument("--csv-dir", default=os.path.join("data", "csv"))
    args = parser.parse_args()

    if not os.path.isfile(args.metadata_csv):
        print(f"metadata.csv not found: {args.metadata_csv}")
        return

    df = pd.read_csv(args.metadata_csv)
    # try common float/platform column names
    float_col = None
    for c in df.columns:
        cl = str(c).lower()
        if "platform" in cl or "float" in cl or cl.endswith("_min") or cl.endswith("_max"):
            if "platform" in cl or "float" in cl:
                float_col = c
                break
    if float_col is None:
        # fallback: look for a column named 'PLATFORM_NUMBER' if flattened
        for c in df.columns:
            if str(c).upper().startswith("PLATFORM"):
                float_col = c
                break
    if float_col is None:
        print("Could not find platform column in metadata.csv")
        return

    platform_numbers = [str(x) for x in df[float_col].dropna().astype(str).tolist()]
    platform_numbers = ["".join(ch for ch in s if ch.isdigit()) for s in platform_numbers]
    platform_numbers = [s for s in platform_numbers if s]
    if not platform_numbers:
        print("No platform numbers found in metadata.csv")
        return

    conn = open_db(args.db_path)
    total = 0
    ingested_from_csv = 0
    try:
        # 1) Prefer ingesting from per-float CSVs if present
        for pid in platform_numbers:
            csv_path = os.path.join(args.csv_dir, f"float_{pid}.csv")
            if os.path.isfile(csv_path):
                try:
                    from scripts.rebuild_argo_sqlite import upsert_from_csv
                except Exception:
                    from rebuild_argo_sqlite import upsert_from_csv
                ingested_from_csv += upsert_from_csv(conn, pid, csv_path)

        # 2) Also scan local NetCDFs for any remaining platforms
        for name in os.listdir(args.argo_dir):
            if not name.endswith(".nc") or name.endswith("_meta.nc"):
                continue
            # include only files with one of the target platform numbers in filename
            if not any(pid in name for pid in platform_numbers):
                continue
            path = os.path.join(args.argo_dir, name)
            try:
                grouped = parse_file(path)
                for pid, rows in grouped.items():
                    if pid in platform_numbers:
                        total += upsert_float_records(conn, pid, rows)
            except Exception as e:
                print(f"Failed to process {name}: {e}")
        conn.commit()
        print(f"Ingested {ingested_from_csv + total} rows (CSV: {ingested_from_csv}, NC: {total}) into {args.db_path}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()


