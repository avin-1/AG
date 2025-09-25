from fastapi import APIRouter
from src.database.query_engine import execute_sql_query, fetch_latest_for_platforms_sqlite
from src.utils.logging import get_logger
from src.api.schema import NearestFloatRequest, NearestFloatResponse, QueryInput
from src.llm.sql_rag_pipeline import SQLRAGPipeline
from src.database.vector_db import init_vector_db, query_nearest_platforms, query_nearest_by_location
import json
from pathlib import Path
import pandas as pd
from pathlib import Path
import math
from typing import Optional, Tuple
from src.llm.models import get_llm, get_hf_router_client, hf_chat_complete

router = APIRouter()
logger = get_logger(__name__)

DB_CONFIG = None  # Not used for SQLite path-based access

# Initialize SQL RAG pipeline
sql_rag_pipeline = None
chroma_collection = None

def get_sql_rag_pipeline():
    """Get or create SQL RAG pipeline instance"""
    global sql_rag_pipeline
    if sql_rag_pipeline is None:
        sql_rag_pipeline = SQLRAGPipeline(DB_CONFIG)
    return sql_rag_pipeline


def get_chroma_collection():
    global chroma_collection
    if chroma_collection is None:
        from src.data_ingestion.metadata_extractor import extract_metadata
        metadata = extract_metadata()
        chroma_collection = init_vector_db(metadata)
    return chroma_collection

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

def _nearest_floats(df: pd.DataFrame, lat: float, lon: float, n: int = 2) -> list:
    """Find the n nearest floats to the given location"""
    lat_col, lon_col, id_col, temp_col, sal_col, depth_min_col, depth_max_col = _pick_columns(df)

    if not lat_col or not lon_col:
        return []

    # Compute distance
    use_cols = [c for c in [id_col, lat_col, lon_col, temp_col, sal_col, depth_min_col, depth_max_col] if c is not None]
    df2 = df[use_cols].dropna(subset=[lat_col, lon_col])
    if df2.empty:
        return []

    def distance(row):
        return _haversine_km(lat, lon, float(row[lat_col]), float(row[lon_col]))

    df2 = df2.assign(_dist_km=df2.apply(distance, axis=1))
    nearest = df2.nsmallest(n, '_dist_km')

    results = []
    for _, row in nearest.iterrows():
        results.append(NearestFloatResponse(
            id=(row[id_col] if id_col else None),
            lat=float(row[lat_col]),
            lon=float(row[lon_col]),
            temperature=(float(row[temp_col]) if temp_col and not pd.isna(row[temp_col]) else None),
            salinity=(float(row[sal_col]) if sal_col and not pd.isna(row[sal_col]) else None),
            depth_min=(float(row[depth_min_col]) if depth_min_col and not pd.isna(row[depth_min_col]) else None),
            depth_max=(float(row[depth_max_col]) if depth_max_col and not pd.isna(row[depth_max_col]) else None),
        ))

    return results

@router.post("/get_nearest_float", response_model=NearestFloatResponse)
async def get_nearest_float(req: NearestFloatRequest):
    df = _load_processed_df()
    if df is None:
        return NearestFloatResponse()
    res = _nearest_float(df, req.lat, req.lon)
    return res or NearestFloatResponse()

@router.post("/get_nearest_floats")
async def get_nearest_floats(req: NearestFloatRequest):
    """Get the 2 nearest floats to the given location"""
    df = _load_processed_df()
    if df is None:
        return {"floats": []}
    floats = _nearest_floats(df, req.lat, req.lon, n=2)
    return {"floats": [f.dict() for f in floats]}

@router.post("/comparative_analysis")
async def comparative_analysis(req: NearestFloatRequest):
    """Get comparative analysis between the 2 nearest floats"""
    df = _load_processed_df()
    if df is None:
        return {"analysis": "No data available.", "floats": []}

    floats = _nearest_floats(df, req.lat, req.lon, n=2)
    if len(floats) < 2:
        return {"analysis": "Not enough nearby floats for comparison.", "floats": [f.dict() for f in floats]}

    profession = (req.profession or "researcher").lower()
    
    # Create comparative analysis prompt
    float1, float2 = floats[0], floats[1]
    
    analysis_prompt = f"""
    Role: {profession}
    Comparative Analysis of Two Nearest ARGO Floats:

    Float 1 (Closest):
    - ID: {float1.id or 'N/A'}
    - Location: {float1.lat:.4f}°N, {float1.lon:.4f}°E
    - Temperature: {float1.temperature if float1.temperature is not None else 'N/A'}°C
    - Salinity: {float1.salinity if float1.salinity is not None else 'N/A'} PSU
    - Depth Range: {float1.depth_min if float1.depth_min is not None else 'N/A'} - {float1.depth_max if float1.depth_max is not None else 'N/A'} m

    Float 2 (Second Closest):
    - ID: {float2.id or 'N/A'}
    - Location: {float2.lat:.4f}°N, {float2.lon:.4f}°E
    - Temperature: {float2.temperature if float2.temperature is not None else 'N/A'}°C
    - Salinity: {float2.salinity if float2.salinity is not None else 'N/A'} PSU
    - Depth Range: {float2.depth_min if float2.depth_min is not None else 'N/A'} - {float2.depth_max if float2.depth_max is not None else 'N/A'} m

    Provide a comparative analysis highlighting:
    1. Key differences between the two floats
    2. What these differences might indicate about ocean conditions
    3. Implications for the user's location
    4. Recommendations based on the data

    Use appropriate language for a {profession}.
    """

    # Get LLM analysis
    client = get_hf_router_client()
    if client is not None:
        analysis = hf_chat_complete(client, model="openai/gpt-oss-20b", prompt=analysis_prompt)
    else:
        llm = get_llm(model_type="openrouter")
        try:
            resp = llm.invoke(analysis_prompt)
            analysis = getattr(resp, "content", str(resp))
        except Exception:
            try:
                analysis = llm.predict(analysis_prompt)
            except Exception:
                try:
                    analysis = llm(analysis_prompt)
                except Exception:
                    analysis = "Unable to perform comparative analysis at the moment."

    return {
        "analysis": analysis,
        "floats": [f.dict() for f in floats]
    }


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
        insights = hf_chat_complete(client, model="openai/gpt-oss-20b", prompt=prompt)
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
        answer = hf_chat_complete(client, model="openai/gpt-oss-20b", prompt=prompt)
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

@router.post("/sql_query")
async def sql_query(req: QueryInput):
    """Enhanced query endpoint using SQL RAG pipeline"""
    try:
        pipeline = get_sql_rag_pipeline()
        
        # Create context from request
        context = {}
        if hasattr(req, 'lat') and hasattr(req, 'lon'):
            context['lat'] = req.lat
            context['lon'] = req.lon
        if hasattr(req, 'profession'):
            context['profession'] = req.profession
        
        # Use Chroma to get nearest platform_numbers for the query text
        collection = get_chroma_collection()
        # Prefer nearest by location if lat/lon present; fallback to text similarity
        nearest_platforms = []
        if 'lat' in context and 'lon' in context and context['lat'] is not None and context['lon'] is not None:
            nearest_platforms = query_nearest_by_location(collection, context['lat'], context['lon'], n_results=3)
        if not nearest_platforms:
            nearest_platforms = query_nearest_platforms(collection, req.text, n_results=3)
        context['nearest_platforms'] = nearest_platforms

        # Load variable catalog if available
        try:
            catalog_path = Path("data/processed/variable_catalog.json")
            if catalog_path.exists():
                context['variable_catalog'] = json.loads(catalog_path.read_text())
        except Exception:
            pass

        # Fetch data directly from SQLite for nearest platforms
        data_rows = fetch_latest_for_platforms_sqlite(nearest_platforms, limit=20)
        # Prepare a simple SQL string representation (for transparency)
        sql_preview = " UNION ALL ".join([f"SELECT * FROM float_{pid}" for pid in nearest_platforms]) + " ORDER BY time DESC LIMIT 20"

        # Map tuples to dicts in known order
        columns = [
            "profile_id",
            "latitude",
            "longitude",
            "time",
            "temperature_avg",
            "salinity_avg",
            "depth_min",
            "depth_max",
            "platform_number",
        ]
        records = [dict(zip(columns, r)) for r in data_rows]

        # Build profession-aware prompt
        profession = (getattr(req, 'profession', None) or "researcher").lower()
        non_technical_roles = {"fisherman", "student", "farmer", "tourist", "parent"}
        policy_roles = {"policymaker", "policy", "administrator"}
        style = (
            "Use plain layman language. Avoid jargon. Keep it short (80-120 words). Explain what it means in everyday terms and what to do next."
            if profession in non_technical_roles
            else (
                "Keep it executive-friendly with minimal jargon. Focus on impacts and actions. Use 3-5 bullets."
                if profession in policy_roles
                else "Use concise scientific language appropriate for a researcher. Include implications and next steps."
            )
        )

        # Summarize top rows for context
        def fmt_row(r: dict) -> str:
            return (
                f"Float {r.get('platform_number','?')} at ({r.get('latitude','?')}, {r.get('longitude','?')}) "
                f"on {r.get('time','?')}: T={r.get('temperature_avg','?')}°C, S={r.get('salinity_avg','?')} PSU, "
                f"Depth {r.get('depth_min','?')}-{r.get('depth_max','?')} m"
            )

        preview_lines = "\n".join([f"- {fmt_row(r)}" for r in records[:10]]) or "- No rows fetched"

        prompt = (
            f"Role: {profession}\n"
            f"User question: {req.text}\n"
            f"Location: lat={context.get('lat')}, lon={context.get('lon')}\n"
            f"Nearest platforms: {', '.join(nearest_platforms) if nearest_platforms else 'N/A'}\n\n"
            f"Recent observations (up to 10):\n{preview_lines}\n\n"
            f"Instructions: {style} Base your answer strictly on the observations above."
        )

        # Call LLM
        client = get_hf_router_client()
        try:
            if client is not None:
                answer = hf_chat_complete(client, model="openai/gpt-oss-20b", prompt=prompt)
            else:
                llm = get_llm(model_type="openrouter")
                try:
                    resp = llm.invoke(prompt)
                    answer = getattr(resp, "content", str(resp))
                except Exception:
                    try:
                        answer = llm.predict(prompt)
                    except Exception:
                        answer = llm(prompt)
        except Exception:
            answer = "Unable to generate an answer at the moment."

        result = {
            "response": answer,
            "sql": sql_preview,
            "data": records,
            "nearest_platforms": nearest_platforms,
            "query_type": "nearest_union",
        }

        return {
            "response": result.get("answer"),
            "sql": result.get("sql"),
            "data": result.get("data"),
            "nearest_platforms": result.get("nearest_platforms", []),
            "query_type": result.get("query_type"),
        }
        
    except Exception as e:
        logger.error(f"SQL query failed: {e}")
        return {"response": "I'm sorry, I couldn't process your query at the moment. Please try again."}

@router.post("/sql_nearest_floats")
async def sql_nearest_floats(req: NearestFloatRequest):
    """Get nearest floats using SQL queries"""
    try:
        pipeline = get_sql_rag_pipeline()
        floats = pipeline.get_nearest_floats(req.lat, req.lon, 2)
        return {"floats": floats}
        
    except Exception as e:
        logger.error(f"SQL nearest floats query failed: {e}")
        return {"floats": []}

@router.post("/sql_comparative_analysis")
async def sql_comparative_analysis(req: NearestFloatRequest):
    """Get comparative analysis using SQL queries"""
    try:
        pipeline = get_sql_rag_pipeline()
        analysis = pipeline.get_comparative_analysis(req.lat, req.lon)
        return analysis
        
    except Exception as e:
        logger.error(f"SQL comparative analysis failed: {e}")
        return {
            "analysis": "Unable to perform analysis at the moment.",
            "floats": []
        }