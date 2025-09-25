import argparse
import csv
import os
from pathlib import Path
from typing import Optional

import netCDF4 as nc


def decode_str(var) -> Optional[str]:
    try:
        data = var[:]
        try:
            s = b"".join(data.astype("S1").reshape(-1)).decode("utf-8", errors="ignore").strip().strip("\x00")
            return s or None
        except Exception:
            return None
    except Exception:
        return None


def extract_from_meta_nc(meta_path: str) -> dict:
    ds = nc.Dataset(meta_path, "r")
    try:
        platform = None
        for key in ("PLATFORM_NUMBER", "platform_number", "platform"):
            if key in ds.variables:
                platform = decode_str(ds.variables[key]) or platform
        if platform is None:
            platform = str(getattr(ds, "platform_number", "")).strip() or None

        md = {
            "platform_number": platform,
            "LATITUDE_min": getattr(ds, "LATITUDE_min", None),
            "LATITUDE_max": getattr(ds, "LATITUDE_max", None),
            "LONGITUDE_min": getattr(ds, "LONGITUDE_min", None),
            "LONGITUDE_max": getattr(ds, "LONGITUDE_max", None),
            "TIME_min": getattr(ds, "TIME_min", None),
            "TIME_max": getattr(ds, "TIME_max", None),
        }
        # Stringify
        for k, v in list(md.items()):
            if v is None:
                md[k] = ""
            else:
                md[k] = str(v)
        return md
    finally:
        ds.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export *_meta.nc metadata to per-float CSVs")
    parser.add_argument("--argo-dir", default="argo_data")
    parser.add_argument("--out-dir", default=str(Path("data") / "csv_meta"))
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    count = 0
    for name in os.listdir(args.argo_dir):
        if not name.endswith("_meta.nc"):
            continue
        path = os.path.join(args.argo_dir, name)
        try:
            md = extract_from_meta_nc(path)
            pid = (md.get("platform_number") or "").strip()
            if not pid:
                # fallback: try to parse from filename
                pid = "".join(ch for ch in name if ch.isdigit())
            if not pid:
                continue
            out_path = os.path.join(args.out_dir, f"float_{pid}_meta.csv")
            write_header = not os.path.exists(out_path)
            with open(out_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "platform_number",
                        "LATITUDE_min",
                        "LATITUDE_max",
                        "LONGITUDE_min",
                        "LONGITUDE_max",
                        "TIME_min",
                        "TIME_max",
                    ],
                )
                if write_header:
                    writer.writeheader()
                writer.writerow(md)
                count += 1
        except Exception as e:
            print(f"Failed to export {name}: {e}")

    print(f"Exported metadata rows: {count} into {args.out_dir}")


if __name__ == "__main__":
    main()


