from fastapi import APIRouter
from src.database.query_engine import execute_sql_query
from src.utils.logging import get_logger
from src.api.schema import NearestFloatRequest, NearestFloatResponse
import pandas as pd
from pathlib import Path
import math

router = APIRouter()
logger = get_logger(__name__)

@router.get("/data")
async def get_data(query: str):
    results = execute_sql_query(query)
    return {"results": results}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


@router.post("/get_nearest_float", response_model=NearestFloatResponse)
async def get_nearest_float(req: NearestFloatRequest):
    processed_path = Path("data/processed/argo_data.parquet")
    if not processed_path.exists():
        return NearestFloatResponse()

    df = pd.read_parquet(processed_path)

    # Heuristic column picking
    lat_col = next((c for c in df.columns if c.lower().startswith('lat')), None)
    lon_col = next((c for c in df.columns if c.lower().startswith('lon')), None)
    id_col = next((c for c in df.columns if 'platform' in c.lower() or 'float' in c.lower() or 'id' in c.lower()), None)
    temp_col = next((c for c in df.columns if 'temp' in c.lower()), None)
    sal_col = next((c for c in df.columns if 'sal' in c.lower()), None)
    depth_min_col = next((c for c in df.columns if 'depth_min' in c.lower() or 'p_min' in c.lower()), None)
    depth_max_col = next((c for c in df.columns if 'depth_max' in c.lower() or 'p_max' in c.lower()), None)

    if not lat_col or not lon_col:
        return NearestFloatResponse()

    # Compute distance
    df = df[[c for c in [id_col, lat_col, lon_col, temp_col, sal_col, depth_min_col, depth_max_col] if c is not None]].dropna(subset=[lat_col, lon_col])
    if df.empty:
        return NearestFloatResponse()

    def distance(row):
        return _haversine_km(req.lat, req.lon, float(row[lat_col]), float(row[lon_col]))

    df = df.assign(_dist_km=df.apply(distance, axis=1))
    best = df.nsmallest(1, '_dist_km').iloc[0]

    return NearestFloatResponse(
        id=(best[id_col] if id_col else None),
        lat=float(best[lat_col]),
        lon=float(best[lon_col]),
        temperature=(float(best[temp_col]) if temp_col and not pd.isna(best[temp_col]) else None),
        salinity=(float(best[sal_col]) if sal_col and not pd.isna(best[sal_col]) else None),
        depth_min=(float(best[depth_min_col]) if depth_min_col and not pd.isna(best[depth_min_col]) else None),
        depth_max=(float(best[depth_max_col]) if depth_max_col and not pd.isna(best[depth_max_col]) else None),
    )