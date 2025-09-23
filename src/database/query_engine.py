import psycopg2
import yaml
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def execute_sql_query(query):
    config = load_config()
    conn_params = config["database"]["postgresql"]
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results

def query_vector_db(collection, query_text, n_results=5):
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results