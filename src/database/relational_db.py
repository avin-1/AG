import psycopg2
import yaml
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def init_db():
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Create table for ARGO data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS argo_data (
            id SERIAL PRIMARY KEY,
            float_id VARCHAR(50),
            latitude FLOAT,
            longitude FLOAT,
            time TIMESTAMP,
            salinity FLOAT,
            temperature FLOAT
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Initialized PostgreSQL database")

def insert_data(df):
    config = load_config()
    conn_params = config["database"]["postgresql"]
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO argo_data (float_id, latitude, longitude, time, salinity, temperature)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (str(row['float']), row['latitude'], row['longitude'], row['time'], row['PSAL'], row['TEMP']))
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Inserted data into PostgreSQL")

if __name__ == "__main__":
    init_db()