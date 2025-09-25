import argparse
import csv
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

import netCDF4 as nc

# Allow running as: `python scripts/nc_to_csv.py` or `python -m scripts.nc_to_csv`
try:
    from scripts.nc_to_sqlite import parse_file
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    try:
        from scripts.nc_to_sqlite import parse_file
    except ModuleNotFoundError:
        from nc_to_sqlite import parse_file


def write_csvs(records_by_platform: Dict[str, List[dict]], out_dir: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for platform, rows in records_by_platform.items():
        if platform == "unknown" or not rows:
            continue
        path = os.path.join(out_dir, f"float_{platform}.csv")
        write_header = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "profile_id",
                    "latitude",
                    "longitude",
                    "time",
                    "depth_min",
                    "depth_max",
                    "temperature_avg",
                    "salinity_avg",
                    "pressure_avg",
                ],
            )
            if write_header:
                writer.writeheader()
            writer.writerows(rows)
            total += len(rows)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Export non-metadata NetCDF files to per-float CSVs")
    parser.add_argument("--argo-dir", default="argo_data")
    parser.add_argument("--out-dir", default=os.path.join("data", "csv"))
    args = parser.parse_args()

    total = 0
    aggregated: Dict[str, List[dict]] = defaultdict(list)
    for name in os.listdir(args.argo_dir):
        if not name.endswith(".nc") or name.endswith("_meta.nc"):
            continue
        path = os.path.join(args.argo_dir, name)
        try:
            grouped = parse_file(path)
            for platform, rows in grouped.items():
                aggregated[platform].extend(rows)
        except Exception as e:
            print(f"Failed to process {name}: {e}")
    total = write_csvs(aggregated, args.out_dir)
    print(f"Exported {total} rows into CSVs under {args.out_dir}")


if __name__ == "__main__":
    main()


