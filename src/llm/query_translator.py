from src.utils.logging import get_logger

logger = get_logger(__name__)

def translate_to_sql(query):
    # Simple rule-based translation for prototype
    if "salinity profiles near the equator" in query.lower():
        return "SELECT * FROM argo_data WHERE latitude BETWEEN -5 AND 5 AND time LIKE '2023-03%'"
    elif "nearest floats to" in query.lower():
        return "SELECT float_id, latitude, longitude FROM argo_data ORDER BY (latitude - 0)^2 + (longitude - 90)^2 LIMIT 5"
    else:
        return "SELECT * FROM argo_data LIMIT 10"