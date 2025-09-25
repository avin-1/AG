from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from src.nearest_floats import get_nearest_platforms
from src.sqlite_fetch import open_db, fetch_multiple


app = FastAPI(title="ARGO Q&A API")


class AnswerRequest(BaseModel):
    query: str
    lat: float
    lon: float
    profession: str
    k: int = 3


def summarize_for_profession(profession: str, query: str, data: Dict[str, List[Dict]]) -> str:
    # Lightweight heuristic summary to avoid external LLM call here.
    # Frontend can swap to a real LLM with the same inputs.
    lines: List[str] = []
    lines.append(f"Profession: {profession}")
    lines.append(f"Question: {query}")
    total_rows = sum(len(v) for v in data.values())
    lines.append(f"Retrieved {total_rows} rows across {len(data)} floats.")
    # Simple aggregates
    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None
    import statistics
    temps: List[float] = []
    salts: List[float] = []
    for rows in data.values():
        for r in rows:
            t = safe_float(r.get("temperature_avg"))
            s = safe_float(r.get("salinity_avg"))
            if t is not None:
                temps.append(t)
            if s is not None:
                salts.append(s)
    if temps:
        lines.append(f"Temperature avg: {statistics.fmean(temps):.2f} C")
    if salts:
        lines.append(f"Salinity avg: {statistics.fmean(salts):.3f} PSU")
    return "\n".join(lines)


@app.post("/answer")
def answer(req: AnswerRequest):
    # 1) Nearest floats via Chroma
    nearest = get_nearest_platforms(req.lat, req.lon, k=req.k)
    platforms = [pid for pid, _ in nearest]
    # 2) Fetch data from SQLite
    conn = open_db("data/argo.db")
    try:
        data = fetch_multiple(conn, platforms, per_float_limit=200)
    finally:
        conn.close()
    # 3) Summarize/answer
    answer_text = summarize_for_profession(req.profession, req.query, data)
    return {
        "platforms": platforms,
        "nearest": nearest,
        "data": data,
        "answer": answer_text,
    }


