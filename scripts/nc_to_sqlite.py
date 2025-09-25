import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import netCDF4 as nc

# Allow running as: `python scripts/nc_to_sqlite.py` or `python -m scripts.nc_to_sqlite`
try:
    from scripts.rebuild_argo_sqlite import (
        open_db,
        upsert_float_records,
    )
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    try:
        from scripts.rebuild_argo_sqlite import (
            open_db,
            upsert_float_records,
        )
    except ModuleNotFoundError:
        # Fallback when running from inside scripts directory directly
        from rebuild_argo_sqlite import (
            open_db,
            upsert_float_records,
        )


def _decode_char_array(var) -> Optional[str]:
    try:
        import numpy as np
        arr = var[:]
        if hasattr(arr, "mask"):
            filler = getattr(arr, "filled", None)
            if callable(filler):
                arr = filler(b" ")
        if arr.dtype.kind in ("S", "U"):
            s = b"".join(arr.astype("S1").reshape(-1)).decode("utf-8", errors="ignore")
            s = s.strip().strip("\x00")
            return s or None
        # If already 1-D array of bytes
        try:
            s = b"".join([bytes([int(x)]) for x in arr.flatten()]).decode("utf-8", errors="ignore")
            s = s.strip().strip("\x00")
            return s or None
        except Exception:
            return None
    except Exception:
        return None


def extract_platform_number(ds: nc.Dataset) -> str:
    # Try common attributes/variables for platform number
    for attr in ("platform_number", "PLATFORM_NUMBER", "platform_id", "platform_id_str"):
        if hasattr(ds, attr):
            val = getattr(ds, attr)
            try:
                return str(val).strip()
            except Exception:
                pass
    for var in ("PLATFORM_NUMBER", "platform_number"):
        if var in ds.variables:
            try:
                var_obj = ds.variables[var]
                s = _decode_char_array(var_obj)
                if s:
                    return s
                data = var_obj[:]
                if getattr(data, "size", 0) >= 1:
                    return str(data.flat[0])
            except Exception:
                pass
    # Fallback to filename cues
    return "unknown"


def sanitize_platform_number(value: str) -> str:
    # Keep digits only; common for ARGO platform numbers
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return digits if digits else "unknown"


def get_var(ds: nc.Dataset, names: List[str]):
    for name in names:
        if name in ds.variables:
            return ds.variables[name][:]
    return None


def safe_item(arr, idx, default=None):
    try:
        return arr[idx]
    except Exception:
        return default


def parse_file(filepath: str) -> Dict[str, List[dict]]:
    ds = nc.Dataset(filepath, "r")
    try:
        platform = sanitize_platform_number(extract_platform_number(ds))

        # Likely variables in ARGO profiles
        lat = get_var(ds, ["LATITUDE", "latitude", "lat"])
        lon = get_var(ds, ["LONGITUDE", "longitude", "lon"])
        juld = get_var(ds, ["JULD", "time", "TIME"])  # days since 1950-01-01 or similar
        # aggregate stats may not exist; we'll fallback to simple means if profile arrays exist
        temp = get_var(ds, ["TEMP", "temperature"])  # per-level
        psal = get_var(ds, ["PSAL", "salinity"])     # per-level
        pres = get_var(ds, ["PRES", "pressure"])     # per-level
        zmin = get_var(ds, ["DEPTH_MIN", "z_min"])   # optional
        zmax = get_var(ds, ["DEPTH_MAX", "z_max"])   # optional

        # profile id heuristic from filename if not available
        profile_id = os.path.splitext(os.path.basename(filepath))[0]

        def to_float(x):
            try:
                return float(x)
            except Exception:
                return None

        # Convert JULD if present; many ARGO use days since 1950-01-01
        from datetime import datetime, timedelta
        time_val = None
        if juld is not None:
            j0 = safe_item(juld, 0)
            try:
                # assume days since 1950-01-01
                time_val = (datetime(1950, 1, 1) + timedelta(days=float(j0))).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_val = None

        # Compute simple averages if arrays present
        import numpy as np
        def avg(arr):
            try:
                a = np.array(arr, dtype=float)
                if a.size == 0:
                    return None
                m = np.nanmean(a)
                return float(m) if not np.isnan(m) else None
            except Exception:
                return None

        temperature_avg = avg(temp) if temp is not None else None
        salinity_avg = avg(psal) if psal is not None else None
        pressure_avg = avg(pres) if pres is not None else None

        # Depth min/max if pressure present (pressure in dbar approx equals depth in meters for simple proxy)
        if zmin is not None:
            depth_min = to_float(safe_item(zmin, 0))
        else:
            depth_min = avg(pres) if pres is not None else None
        if zmax is not None:
            depth_max = to_float(safe_item(zmax, 0))
        else:
            depth_max = avg(pres) if pres is not None else None

        record = {
            "profile_id": profile_id,
            "latitude": to_float(safe_item(lat, 0) if lat is not None else None),
            "longitude": to_float(safe_item(lon, 0) if lon is not None else None),
            "time": time_val,
            "depth_min": depth_min,
            "depth_max": depth_max,
            "temperature_avg": temperature_avg,
            "salinity_avg": salinity_avg,
            "pressure_avg": pressure_avg,
        }

        return {platform: [record]}
    finally:
        ds.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert ARGO NetCDF files to per-float SQLite tables")
    parser.add_argument("--db-path", default=os.path.join("data", "argo.db"))
    parser.add_argument("--argo-dir", default="argo_data")
    args = parser.parse_args()

    conn = open_db(args.db_path)
    try:
        total = 0
        for name in os.listdir(args.argo_dir):
            # Skip metadata files explicitly
            if name.endswith("_meta.nc"):
                continue
            if not name.endswith(".nc"):
                continue
            path = os.path.join(args.argo_dir, name)
            try:
                grouped = parse_file(path)
                for platform, records in grouped.items():
                    if platform == "unknown":
                        # skip files where platform number can't be determined
                        continue
                    total += upsert_float_records(conn, platform, records)
            except Exception as e:
                print(f"Failed to process {name}: {e}")
        conn.commit()
        print(f"Done. Upserted {total} records into {args.db_path}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()


