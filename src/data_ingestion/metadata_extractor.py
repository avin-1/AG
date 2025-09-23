import pandas as pd
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def extract_metadata():
    processed_path = Path("data/processed")
    df = pd.read_parquet(processed_path / "argo_data.parquet")
    
    # Check what columns are available
    logger.info(f"Available columns: {df.columns.tolist()}")
    
    # Try to find the correct column names for ARGO data
    # ARGO data typically has PLATFORM_NUMBER, LATITUDE, LONGITUDE, TIME
    float_col = None
    lat_col = None
    lon_col = None
    time_col = None
    
    # Look for common ARGO column names
    for col in df.columns:
        col_lower = col.lower()
        if 'platform' in col_lower or 'float' in col_lower:
            float_col = col
        elif 'lat' in col_lower:
            lat_col = col
        elif 'lon' in col_lower:
            lon_col = col
        elif 'time' in col_lower:
            time_col = col
    
    logger.info(f"Found columns - Float: {float_col}, Lat: {lat_col}, Lon: {lon_col}, Time: {time_col}")
    
    if float_col and lat_col and lon_col and time_col:
        # Generate metadata grouped by float/platform
        metadata = df.groupby(float_col).agg({
            lat_col: ['min', 'max'],
            lon_col: ['min', 'max'],
            time_col: ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        metadata.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in metadata.columns]
        
        metadata.to_csv(processed_path / "metadata.csv")
        logger.info("Extracted metadata to metadata.csv")
        return metadata
    else:
        logger.warning("Could not find required columns for metadata extraction")
        # Create basic metadata with available columns
        basic_metadata = {
            'total_records': len(df),
            'columns': df.columns.tolist(),
            'date_range': f"{df[time_col].min()} to {df[time_col].max()}" if time_col else "Unknown"
        }
        logger.info(f"Basic metadata: {basic_metadata}")
        return basic_metadata

if __name__ == "__main__":
    extract_metadata()