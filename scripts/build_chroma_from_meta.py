import argparse
import os
from typing import Optional, Dict

import chromadb
from chromadb.utils import embedding_functions

try:
    import netCDF4 as nc  # optional; we will skip files if unreadable
except Exception:
    nc = None  # type: ignore


def decode_char_var(var) -> Optional[str]:
    try:
        data = var[:]
        try:
            s = b"".join(data.astype("S1").reshape(-1)).decode("utf-8", errors="ignore").strip().strip("\x00")
            return s or None
        except Exception:
            return None
    except Exception:
        return None


def extract_from_meta_nc(path: str) -> Dict[str, Optional[str]]:
    if nc is None:
        return {}
    try:
        ds = nc.Dataset(path, "r")
    except Exception:
        return {}
    try:
        platform = None
        for key in ("PLATFORM_NUMBER", "platform_number", "platform"):
            if key in ds.variables:
                platform = decode_char_var(ds.variables[key]) or platform
        if platform is None:
            platform = str(getattr(ds, "platform_number", "")).strip() or None

        md = {
            "platform_number": platform,
            "LATITUDE_min": str(getattr(ds, "LATITUDE_min", "") or ""),
            "LATITUDE_max": str(getattr(ds, "LATITUDE_max", "") or ""),
            "LONGITUDE_min": str(getattr(ds, "LONGITUDE_min", "") or ""),
            "LONGITUDE_max": str(getattr(ds, "LONGITUDE_max", "") or ""),
            "TIME_min": str(getattr(ds, "TIME_min", "") or ""),
            "TIME_max": str(getattr(ds, "TIME_max", "") or ""),
        }
        return md
    finally:
        try:
            ds.close()
        except Exception:
            pass


def platform_from_filename(name: str) -> Optional[str]:
    digits = "".join(ch for ch in name if ch.isdigit())
    return digits or None


def build_collection(argo_dir: str, chroma_dir: str, collection_name: str, reset: bool) -> int:
    client = chromadb.PersistentClient(path=chroma_dir)
    emb = embedding_functions.DefaultEmbeddingFunction()

    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        collection = client.create_collection(collection_name, embedding_function=emb)

    added = 0
    for name in os.listdir(argo_dir):
        if not name.endswith("_meta.nc"):
            continue
        path = os.path.join(argo_dir, name)
        md = extract_from_meta_nc(path)
        pid = md.get("platform_number") if md else None
        if not pid:
            pid = platform_from_filename(name)
        if not pid:
            continue

        # Build concise document text
        doc = (
            f"Float {pid}: "
            f"Lat {md.get('LATITUDE_min','?') if md else '?'}–{md.get('LATITUDE_max','?') if md else '?'}, "
            f"Lon {md.get('LONGITUDE_min','?') if md else '?'}–{md.get('LONGITUDE_max','?') if md else '?'}, "
            f"Time {md.get('TIME_min','?') if md else '?'}–{md.get('TIME_max','?') if md else '?'}"
        )

        # Upsert behavior: delete id first to avoid duplicates
        try:
            collection.delete(ids=[str(pid)])
        except Exception:
            pass
        collection.add(documents=[doc], ids=[str(pid)], metadatas=[{"platform_number": str(pid)}])
        added += 1

    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChromaDB collection from *_meta.nc files only")
    parser.add_argument("--argo-dir", default="argo_data")
    parser.add_argument("--chroma-dir", default="chroma_db")
    parser.add_argument("--collection", default="argo_metadata")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the collection")
    args = parser.parse_args()

    added = build_collection(args.argo_dir, args.chroma_dir, args.collection, args.reset)
    print(f"Indexed {added} metadata docs into Chroma collection '{args.collection}' at {args.chroma_dir}")


if __name__ == "__main__":
    main()


