from fastapi import APIRouter
from src.database.query_engine import execute_sql_query
from src.utils.logging import get_logger
from src.api.schema import NearestFloatRequest, NearestFloatResponse, QueryInput
import pandas as pd
from pathlib import Path
import math
from typing import Optional, Tuple
from src.llm.models import get_llm, get_hf_router_client, hf_chat_complete

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


def _load_processed_df() -> Optional[pd.DataFrame]:
    processed_path = Path("data/processed/argo_data.parquet")
    if not processed_path.exists():
        return None

    df = pd.read_parquet(processed_path)
    return df

def _pick_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    lat_col = next((c for c in df.columns if c.lower().startswith('lat')), None)
    lon_col = next((c for c in df.columns if c.lower().startswith('lon')), None)
    id_col = next((c for c in df.columns if 'platform' in c.lower() or 'float' in c.lower() or 'id' in c.lower()), None)
    temp_col = next((c for c in df.columns if 'temp' in c.lower()), None)
    sal_col = next((c for c in df.columns if 'sal' in c.lower()), None)
    depth_min_col = next((c for c in df.columns if 'depth_min' in c.lower() or 'p_min' in c.lower()), None)
    depth_max_col = next((c for c in df.columns if 'depth_max' in c.lower() or 'p_max' in c.lower()), None)
    return lat_col, lon_col, id_col, temp_col, sal_col, depth_min_col, depth_max_col

def _nearest_float(df: pd.DataFrame, lat: float, lon: float) -> Optional[NearestFloatResponse]:
    lat_col, lon_col, id_col, temp_col, sal_col, depth_min_col, depth_max_col = _pick_columns(df)

    if not lat_col or not lon_col:
        return None

    # Compute distance
    use_cols = [c for c in [id_col, lat_col, lon_col, temp_col, sal_col, depth_min_col, depth_max_col] if c is not None]
    df2 = df[use_cols].dropna(subset=[lat_col, lon_col])
    if df2.empty:
        return None

    def distance(row):
        return _haversine_km(lat, lon, float(row[lat_col]), float(row[lon_col]))

    df2 = df2.assign(_dist_km=df2.apply(distance, axis=1))
    best = df2.nsmallest(1, '_dist_km').iloc[0]

    return NearestFloatResponse(
        id=(best[id_col] if id_col else None),
        lat=float(best[lat_col]),
        lon=float(best[lon_col]),
        temperature=(float(best[temp_col]) if temp_col and not pd.isna(best[temp_col]) else None),
        salinity=(float(best[sal_col]) if sal_col and not pd.isna(best[sal_col]) else None),
        depth_min=(float(best[depth_min_col]) if depth_min_col and not pd.isna(best[depth_min_col]) else None),
        depth_max=(float(best[depth_max_col]) if depth_max_col and not pd.isna(best[depth_max_col]) else None),
    )

@router.post("/get_nearest_float", response_model=NearestFloatResponse)
async def get_nearest_float(req: NearestFloatRequest):
    df = _load_processed_df()
    if df is None:
        return NearestFloatResponse()
    res = _nearest_float(df, req.lat, req.lon)
    return res or NearestFloatResponse()


@router.post("/analyze_location")
async def analyze_location(req: NearestFloatRequest):
    """
    Given lat/lon/profession, find nearest float and ask LLM (DeepSeek via OpenRouter) for insights.
    """
    df = _load_processed_df()
    if df is None:
        return {"insights": "No data available.", "nearest": None}

    nearest = _nearest_float(df, req.lat, req.lon)
    if nearest is None:
        return {"insights": "No nearby float found.", "nearest": None}

    profession = (req.profession or "researcher").lower()

    # Style rules by audience
    non_technical_roles = {"fisherman", "student", "farmer", "tourist", "parent"}
    policy_roles = {"policymaker", "policy", "administrator"}
    is_non_technical = profession in non_technical_roles
    is_policy = profession in policy_roles

    style = (
        "Use plain layman language. Avoid jargon. Keep it short (80-120 words). "
        "Explain what it means in everyday terms and what to do next."
        if is_non_technical
        else (
            "Keep it executive-friendly with minimal jargon. Focus on impacts and actions. "
            "Use 3-5 bullets."
            if is_policy
            else "Use concise scientific language appropriate for a researcher. Include implications and next steps."
        )
    )

    prompt = (
        f"Role: {profession}\n"
        f"You will produce insights tailored to this role based on one ocean float observation. {style}\n\n"
        f"Observation (approx.):\n"
        f"- Float ID: {nearest.id or 'N/A'}\n"
        f"- Coordinates: {nearest.lat:.4f}, {nearest.lon:.4f}\n"
        f"- Temperature: {nearest.temperature if nearest.temperature is not None else 'N/A'}\n"
        f"- Salinity: {nearest.salinity if nearest.salinity is not None else 'N/A'}\n"
        f"- Depth range: {nearest.depth_min if nearest.depth_min is not None else 'N/A'} - {nearest.depth_max if nearest.depth_max is not None else 'N/A'}\n\n"
        "Output format (Markdown):\n"
        "- A short paragraph summary.\n"
        "- 3-5 bullet points with key takeaways.\n"
        "- A final line: 'Next steps:' with 1-2 brief actions."
    )

    # Prefer Hugging Face Router; fallback to previous LLM if HF not configured
    insights: str
    client = get_hf_router_client()
    if client is not None:
        insights = hf_chat_complete(client, model="openai/gpt-oss-120b:fireworks-ai", prompt=prompt)
    else:
        llm = get_llm(model_type="openrouter")
        try:
            resp = llm.invoke(prompt)
            insights = getattr(resp, "content", str(resp))
        except Exception:
            try:
                insights = llm.predict(prompt)
            except Exception:
                try:
                    insights = llm(prompt)
                except Exception:
                    insights = "Unable to fetch insights at the moment."

    return {"insights": insights, "nearest": nearest.dict()}


@router.post("/ask_with_context")
async def ask_with_context(req: QueryInput):
    df = _load_processed_df()
    if df is None:
        return {"response": "No data available to answer your question."}

    nearest = _nearest_float(df, req.lat, req.lon)
    if nearest is None:
        return {"response": "No nearby float found to answer your question."}

    profession = (req.profession or "researcher").lower()
    style = (
        "Use plain layman language. Keep it short and avoid jargon."
        if profession in {"fisherman", "student", "farmer", "tourist", "parent"}
        else "Be concise and professional."
    )

    prompt = (
        f"Role: {profession}\n"
        f"User question: {req.text}\n\n"
        f"Context from nearest ocean float (approx.):\n"
        f"- Float ID: {nearest.id or 'N/A'}\n"
        f"- Coordinates: {nearest.lat:.4f}, {nearest.lon:.4f}\n"
        f"- Temperature: {nearest.temperature if nearest.temperature is not None else 'N/A'}\n"
        f"- Salinity: {nearest.salinity if nearest.salinity is not None else 'N/A'}\n"
        f"- Depth range: {nearest.depth_min if nearest.depth_min is not None else 'N/A'} - {nearest.depth_max if nearest.depth_max is not None else 'N/A'}\n\n"
        f"Answer the user question directly. {style} If the context is insufficient, say what additional data would help."
    )

    client = get_hf_router_client()
    if client is not None:
        answer = hf_chat_complete(client, model="openai/gpt-oss-120b:fireworks-ai", prompt=prompt)
    else:
        llm = get_llm(model_type="openrouter")
        try:
            resp = llm.invoke(prompt)
            answer = getattr(resp, "content", str(resp))
        except Exception:
            try:
                answer = llm.predict(prompt)
            except Exception:
                try:
                    answer = llm(prompt)
                except Exception:
                    answer = "Unable to answer at the moment."

    return {"response": answer}