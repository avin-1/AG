import argparse
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions
import netCDF4 as nc
import csv


def list_platforms_from_csv(csv_dir: str) -> set[str]:
    platforms: set[str] = set()
    if not os.path.isdir(csv_dir):
        return platforms
    for name in os.listdir(csv_dir):
        if not name.endswith('.csv'):
            continue
        if not name.startswith('float_'):
            continue
        pid = name[len('float_'):-len('.csv')]
        if pid.isdigit():
            platforms.add(pid)
    return platforms


def find_meta_file(argo_dir: str, platform_number: str) -> Optional[str]:
    candidates = [
        f"{platform_number}_meta.nc",
        f"R{platform_number}_meta.nc",
        f"D{platform_number}_meta.nc",
        f"META_{platform_number}.nc",
    ]
    for cand in candidates:
        path = os.path.join(argo_dir, cand)
        if os.path.isfile(path):
            return path
    # Fallback: any file ending with _meta.nc that contains platform number
    for name in os.listdir(argo_dir):
        if name.endswith('_meta.nc') and platform_number in name:
            return os.path.join(argo_dir, name)
    return None


def decode_str(var) -> Optional[str]:
    try:
        data = var[:]
        try:
            s = b"".join(data.astype('S1').reshape(-1)).decode('utf-8', errors='ignore').strip().strip('\x00')
            return s or None
        except Exception:
            return None
    except Exception:
        return None


def extract_metadata_from_meta_nc(meta_path: str) -> Dict[str, Optional[str]]:
    ds = nc.Dataset(meta_path, 'r')
    try:
        # Attempt to read common attributes/vars
        plat = None
        for key in ('PLATFORM_NUMBER', 'platform_number', 'platform'):  # may be char array
            if key in ds.variables:
                plat = decode_str(ds.variables[key]) or plat
        if plat is None:
            plat = str(getattr(ds, 'platform_number', '')).strip() or None

        # Try lat/lon/time ranges from meta; if absent, leave None
        lat_min = getattr(ds, 'LATITUDE_min', None)
        lat_max = getattr(ds, 'LATITUDE_max', None)
        lon_min = getattr(ds, 'LONGITUDE_min', None)
        lon_max = getattr(ds, 'LONGITUDE_max', None)
        time_min = getattr(ds, 'TIME_min', None)
        time_max = getattr(ds, 'TIME_max', None)

        md = {
            'platform_number': plat,
            'LATITUDE_min': str(lat_min) if lat_min is not None else None,
            'LATITUDE_max': str(lat_max) if lat_max is not None else None,
            'LONGITUDE_min': str(lon_min) if lon_min is not None else None,
            'LONGITUDE_max': str(lon_max) if lon_max is not None else None,
            'TIME_min': str(time_min) if time_min is not None else None,
            'TIME_max': str(time_max) if time_max is not None else None,
        }
        return md
    finally:
        ds.close()


def fallback_metadata_from_csv(csv_path: str) -> Dict[str, Optional[str]]:
    lat_min = lat_max = lon_min = lon_max = None
    time_min = time_max = None
    def to_float(x):
        try:
            return float(x)
        except Exception:
            return None
    def upd_minmax(val, cur_min, cur_max):
        if val is None:
            return cur_min, cur_max
        cur_min = val if cur_min is None or val < cur_min else cur_min
        cur_max = val if cur_max is None or val > cur_max else cur_max
        return cur_min, cur_max
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = to_float(row.get('latitude'))
            lon = to_float(row.get('longitude'))
            lat_min, lat_max = upd_minmax(lat, lat_min, lat_max)
            lon_min, lon_max = upd_minmax(lon, lon_min, lon_max)
            t = row.get('time')
            if t:
                time_min = t if time_min is None or t < time_min else time_min
                time_max = t if time_max is None or t > time_max else time_max
    return {
        'LATITUDE_min': str(lat_min) if lat_min is not None else None,
        'LATITUDE_max': str(lat_max) if lat_max is not None else None,
        'LONGITUDE_min': str(lon_min) if lon_min is not None else None,
        'LONGITUDE_max': str(lon_max) if lon_max is not None else None,
        'TIME_min': time_min,
        'TIME_max': time_max,
    }


def upsert_chroma(metadata_items: Dict[str, Dict[str, Optional[str]]], chroma_path: str = './chroma_db') -> None:
    client = chromadb.PersistentClient(path=chroma_path)
    emb = embedding_functions.DefaultEmbeddingFunction()
    try:
        collection = client.get_collection('argo_metadata')
    except Exception:
        collection = client.create_collection('argo_metadata', embedding_function=emb)

    ids = []
    docs = []
    metadatas = []
    for pid, md in metadata_items.items():
        doc = (
            f"Float {pid}: Lat {md.get('LATITUDE_min','?')}–{md.get('LATITUDE_max','?')}, "
            f"Lon {md.get('LONGITUDE_min','?')}–{md.get('LONGITUDE_max','?')}, "
            f"Time {md.get('TIME_min','?')}–{md.get('TIME_max','?')}"
        )
        ids.append(str(pid))
        docs.append(doc)
        metadatas.append({"platform_number": str(pid)})

    # Upsert by deleting existing ids first to avoid duplicates
    if ids:
        try:
            collection.delete(ids=ids)
        except Exception:
            pass
        collection.add(documents=docs, ids=ids, metadatas=metadatas)


def main() -> None:
    parser = argparse.ArgumentParser(description='Index ARGO metadata into ChromaDB. Supports *_meta.nc or meta CSVs.')
    parser.add_argument('--argo-dir', default='argo_data', help='Directory with *_meta.nc')
    parser.add_argument('--csv-dir', default=str(Path('data') / 'csv'), help='Directory with per-float data CSVs to filter platforms')
    parser.add_argument('--meta-csv-dir', default=str(Path('data') / 'csv_meta'), help='Directory with per-float metadata CSVs (optional)')
    parser.add_argument('--skip-meta', action='store_true', help='Skip reading *_meta.nc and use only CSV-derived extents')
    args = parser.parse_args()

    platforms = list_platforms_from_csv(args.csv_dir)
    if not platforms:
        print('No platform CSVs found; nothing to index.')
        return

    items: Dict[str, Dict[str, Optional[str]]] = {}
    for pid in sorted(platforms):
        md: Optional[Dict[str, Optional[str]]] = None
        # Prefer metadata CSV if available
        meta_csv_path = os.path.join(args.meta_csv_dir, f'float_{pid}_meta.csv')
        if os.path.isfile(meta_csv_path):
            # Read last row (latest export)
            try:
                with open(meta_csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        md = {
                            'platform_number': row.get('platform_number') or pid,
                            'LATITUDE_min': row.get('LATITUDE_min'),
                            'LATITUDE_max': row.get('LATITUDE_max'),
                            'LONGITUDE_min': row.get('LONGITUDE_min'),
                            'LONGITUDE_max': row.get('LONGITUDE_max'),
                            'TIME_min': row.get('TIME_min'),
                            'TIME_max': row.get('TIME_max'),
                        }
            except Exception:
                md = None
        # If not available, read *_meta.nc directly unless skipping
        if md is None and not args.skip_meta:
            meta_path = find_meta_file(args.argo_dir, pid)
            if meta_path and os.path.isfile(meta_path):
                md = extract_metadata_from_meta_nc(meta_path)
        # Enrich/fallback with data CSV extents
        csv_path = os.path.join(args.csv_dir, f'float_{pid}.csv')
        if os.path.isfile(csv_path):
            ext = fallback_metadata_from_csv(csv_path)
            if md is None:
                md = {'platform_number': pid}
            md.update({k: v for k, v in ext.items() if v is not None})
        if md is not None:
            md['platform_number'] = md.get('platform_number') or pid
            items[pid] = md

    upsert_chroma(items)
    print(f'Indexed {len(items)} platforms into ChromaDB (argo_metadata).')


if __name__ == '__main__':
    main()


