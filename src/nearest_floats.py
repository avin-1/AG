import math
from typing import List, Tuple

import chromadb


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_nearest_platforms(lat: float, lon: float, k: int = 3, chroma_path: str = "./chroma_db") -> List[Tuple[str, float]]:
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection("argo_metadata")
    # We stored documents like: "Float <pid>: Lat a–b, Lon c–d, Time ..."
    # Use naive vector search against a textual location cue, then re-rank by haversine using stored metadata extents
    q = f"lat {lat:.3f} lon {lon:.3f}"
    res = collection.query(query_texts=[q], n_results=max(k * 5, k))
    ids = res.get("ids", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    candidates: List[Tuple[str, float]] = []
    for pid, md in zip(ids, metadatas):
        try:
            # Use midpoints of extents when available
            lat_min = float(md.get("LATITUDE_min")) if md.get("LATITUDE_min") is not None else None
            lat_max = float(md.get("LATITUDE_max")) if md.get("LATITUDE_max") is not None else None
            lon_min = float(md.get("LONGITUDE_min")) if md.get("LONGITUDE_min") is not None else None
            lon_max = float(md.get("LONGITUDE_max")) if md.get("LONGITUDE_max") is not None else None
            if None in (lat_min, lat_max, lon_min, lon_max):
                # If extents missing, skip precise distance and keep as large distance so it sorts later
                distance = float("inf")
            else:
                plat_lat = (lat_min + lat_max) / 2.0
                plat_lon = (lon_min + lon_max) / 2.0
                distance = haversine_km(lat, lon, plat_lat, plat_lon)
            candidates.append((str(pid), distance))
        except Exception:
            continue
    candidates.sort(key=lambda x: x[1])
    return candidates[:k]


