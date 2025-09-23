from pathlib import Path
import argopy
import pandas as pd
import xarray as xr
import yaml
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def ingest_argo_data():
    config = load_config()
    raw_path = Path(config["data"]["raw_path"])
    processed_path = Path(config["data"]["processed_path"])
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Fetch sample ARGO data (Indian Ocean subset)
    # Region format: [lon_min, lon_max, lat_min, lat_max, depth_min, depth_max, time_start, time_end]
    # Indian Ocean: longitude 40-100E, latitude -20 to 20N
    ds = argopy.DataFetcher().region([40, 100, -20, 20, 0, 1000, '2023-03', '2023-04']).to_xarray()
    
    # Convert to DataFrame
    df = ds.to_dataframe()
    
    # Save to Parquet
    output_file = processed_path / "argo_data.parquet"
    df.to_parquet(output_file)
    logger.info(f"Saved processed data to {output_file}")

if __name__ == "__main__":
    ingest_argo_data()