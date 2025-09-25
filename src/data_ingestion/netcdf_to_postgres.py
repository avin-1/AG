#!/usr/bin/env python3
"""
NetCDF to PostgreSQL Conversion System for ARGO Data
Converts NetCDF files to PostgreSQL for efficient querying by LLM
"""

import os
import sys
import pandas as pd
import numpy as np
import netCDF4 as nc
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logging import get_logger

logger = get_logger(__name__)

class NetCDFToPostgreSQL:
    """Convert NetCDF ARGO files to PostgreSQL database"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close_db(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create PostgreSQL tables for ARGO data. Spatial indexes are optional."""
        base_sql = """
        -- Drop existing tables if they exist
        DROP TABLE IF EXISTS argo_profiles CASCADE;
        DROP TABLE IF EXISTS argo_metadata CASCADE;
        DROP TABLE IF EXISTS argo_measurements CASCADE;
        
        -- Create metadata table
        CREATE TABLE argo_metadata (
            id SERIAL PRIMARY KEY,
            platform_number VARCHAR(20) NOT NULL,
            latitude_min DECIMAL(10, 6),
            latitude_max DECIMAL(10, 6),
            longitude_min DECIMAL(10, 6),
            longitude_max DECIMAL(10, 6),
            time_min TIMESTAMP,
            time_max TIMESTAMP,
            file_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create profiles table
        CREATE TABLE argo_profiles (
            id SERIAL PRIMARY KEY,
            platform_number VARCHAR(20) NOT NULL,
            profile_id VARCHAR(50),
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            time TIMESTAMP,
            depth_min DECIMAL(8, 2),
            depth_max DECIMAL(8, 2),
            temperature_avg DECIMAL(8, 3),
            salinity_avg DECIMAL(8, 3),
            pressure_avg DECIMAL(8, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create measurements table for detailed data
        CREATE TABLE argo_measurements (
            id SERIAL PRIMARY KEY,
            platform_number VARCHAR(20) NOT NULL,
            profile_id VARCHAR(50),
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            time TIMESTAMP,
            depth DECIMAL(8, 2),
            pressure DECIMAL(8, 2),
            temperature DECIMAL(8, 3),
            salinity DECIMAL(8, 3),
            quality_flag INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create non-spatial indexes for efficient querying
        CREATE INDEX idx_argo_metadata_platform ON argo_metadata(platform_number);
        CREATE INDEX idx_argo_metadata_location ON argo_metadata(latitude_min, longitude_min);
        CREATE INDEX idx_argo_metadata_time ON argo_metadata(time_min, time_max);
        
        CREATE INDEX idx_argo_profiles_platform ON argo_profiles(platform_number);
        CREATE INDEX idx_argo_profiles_location ON argo_profiles(latitude, longitude);
        CREATE INDEX idx_argo_profiles_time ON argo_profiles(time);
        
        CREATE INDEX idx_argo_measurements_platform ON argo_measurements(platform_number);
        CREATE INDEX idx_argo_measurements_location ON argo_measurements(latitude, longitude);
        CREATE INDEX idx_argo_measurements_time ON argo_measurements(time);
        CREATE INDEX idx_argo_measurements_depth ON argo_measurements(depth);
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(base_sql)
            self.connection.commit()

            # Conditionally create spatial indexes if PostGIS is available
            try:
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis';")
                has_postgis = cursor.fetchone() is not None
                if has_postgis:
                    spatial_sql = """
                    CREATE INDEX IF NOT EXISTS idx_argo_metadata_geom ON argo_metadata USING GIST (
                        ST_Point(longitude_min, latitude_min)
                    );
                    CREATE INDEX IF NOT EXISTS idx_argo_profiles_geom ON argo_profiles USING GIST (
                        ST_Point(longitude, latitude)
                    );
                    CREATE INDEX IF NOT EXISTS idx_argo_measurements_geom ON argo_measurements USING GIST (
                        ST_Point(longitude, latitude)
                    );
                    """
                    cursor.execute(spatial_sql)
                    self.connection.commit()
                    logger.info("PostGIS detected; spatial indexes created")
                else:
                    logger.info("PostGIS not detected; skipping spatial indexes")
            except Exception as e:
                logger.info(f"Skipping spatial indexes (PostGIS unavailable): {e}")
                self.connection.rollback()

            cursor.close()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def extract_netcdf_data(self, filepath: str) -> Dict[str, Any]:
        """Extract data from NetCDF file"""
        try:
            with nc.Dataset(filepath, 'r') as dataset:
                data = {}
                
                # Extract global attributes
                data['global_attrs'] = {}
                for attr in dataset.ncattrs():
                    data['global_attrs'][attr] = getattr(dataset, attr)
                
                # Extract variables
                data['variables'] = {}
                for var_name in dataset.variables:
                    var = dataset.variables[var_name]
                    data['variables'][var_name] = {
                        'shape': var.shape,
                        'dimensions': var.dimensions,
                        'attributes': {attr: getattr(var, attr) for attr in var.ncattrs()},
                        'data': var[:] if var.size < 10000 else None  # Limit data size
                    }
                
                return data
                
        except Exception as e:
            logger.error(f"Failed to extract data from {filepath}: {e}")
            return {}
    
    def process_argo_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Process a single ARGO NetCDF file and return structured data"""
        try:
            data = self.extract_netcdf_data(filepath)
            if not data:
                return []
            
            # Extract platform number from filename or global attributes
            filename = os.path.basename(filepath)
            platform_number = None
            
            # Try to extract platform number from filename
            if '_meta.nc' in filename:
                platform_number = filename.replace('_meta.nc', '')
            elif filename.startswith('D') and '_' in filename:
                platform_number = filename.split('_')[0][1:]  # Remove 'D' prefix
            elif filename.startswith('R') and '_' in filename:
                platform_number = filename.split('_')[0][1:]  # Remove 'R' prefix
            
            # Try to get platform number from global attributes
            if not platform_number and 'global_attrs' in data:
                attrs = data['global_attrs']
                platform_number = attrs.get('platform_number', attrs.get('PLATFORM_NUMBER'))
            
            if not platform_number:
                logger.warning(f"Could not determine platform number for {filepath}")
                return []
            
            # Process the data based on file type
            if '_meta.nc' in filename:
                return self.process_metadata_file(data, platform_number, filepath)
            elif filename.startswith('D'):
                return self.process_data_file(data, platform_number, filepath)
            elif filename.startswith('R'):
                return self.process_realtime_file(data, platform_number, filepath)
            else:
                logger.warning(f"Unknown file type: {filename}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to process {filepath}: {e}")
            return []
    
    def process_metadata_file(self, data: Dict, platform_number: str, filepath: str) -> List[Dict]:
        """Process metadata NetCDF file"""
        results = []
        
        try:
            # Extract metadata information
            metadata = {
                'platform_number': platform_number,
                'file_path': filepath,
                'latitude_min': None,
                'latitude_max': None,
                'longitude_min': None,
                'longitude_max': None,
                'time_min': None,
                'time_max': None
            }
            
            # Extract coordinate and time information
            variables = data.get('variables', {})
            
            # Look for latitude/longitude variables
            for var_name, var_data in variables.items():
                if 'lat' in var_name.lower():
                    lat_data = var_data.get('data')
                    if lat_data is not None and lat_data.size > 0:
                        metadata['latitude_min'] = float(np.min(lat_data))
                        metadata['latitude_max'] = float(np.max(lat_data))
                elif 'lon' in var_name.lower():
                    lon_data = var_data.get('data')
                    if lon_data is not None and lon_data.size > 0:
                        metadata['longitude_min'] = float(np.min(lon_data))
                        metadata['longitude_max'] = float(np.max(lon_data))
                elif 'time' in var_name.lower():
                    time_data = var_data.get('data')
                    if time_data is not None and time_data.size > 0:
                        # Convert time to datetime if possible
                        try:
                            time_min = datetime.fromtimestamp(float(np.min(time_data)))
                            time_max = datetime.fromtimestamp(float(np.max(time_data)))
                            metadata['time_min'] = time_min
                            metadata['time_max'] = time_max
                        except:
                            pass
            
            results.append(metadata)
            
        except Exception as e:
            logger.error(f"Failed to process metadata file {filepath}: {e}")
        
        return results
    
    def process_data_file(self, data: Dict, platform_number: str, filepath: str) -> List[Dict]:
        """Process data NetCDF file (D prefix)"""
        results = []
        
        try:
            # Prefer standard ARGO variable names by reopening the dataset for robust parsing
            try:
                with nc.Dataset(filepath, 'r') as ds:
                    def pick(names):
                        for n in names:
                            if n in ds.variables:
                                return ds.variables[n][:]
                        return None

                    lat = pick(['LATITUDE', 'latitude', 'lat'])
                    lon = pick(['LONGITUDE', 'longitude', 'lon'])
                    juld = pick(['JULD', 'TIME', 'time'])
                    pres = pick(['PRES', 'pres', 'PRESSURE', 'pressure'])
                    temp = pick(['TEMP', 'temperature', 'TEMP_ADJUSTED'])
                    psal = pick(['PSAL', 'salinity', 'PSAL_ADJUSTED'])

                    # Build a single-profile summary per file (simple, but ensures non-empty rows)
                    latitude = float(np.nanmean(lat)) if lat is not None else None
                    longitude = float(np.nanmean(lon)) if lon is not None else None

                    # Convert JULD (days since 1950-01-01) if detected
                    file_time = None
                    if juld is not None:
                        try:
                            juld_mean = float(np.nanmean(juld))
                            base = datetime(1950, 1, 1)
                            file_time = base + pd.to_timedelta(juld_mean, unit='D')
                        except Exception:
                            try:
                                file_time = datetime.fromtimestamp(float(np.nanmean(juld)))
                            except Exception:
                                file_time = None

                    pressure_avg = float(np.nanmean(pres)) if pres is not None else None
                    temperature_avg = float(np.nanmean(temp)) if temp is not None else None
                    salinity_avg = float(np.nanmean(psal)) if psal is not None else None

                    depth_min = float(np.nanmin(pres)) if pres is not None else None
                    depth_max = float(np.nanmax(pres)) if pres is not None else None

                    profile_data = {
                        'platform_number': platform_number,
                        'profile_id': f"{platform_number}_{os.path.basename(filepath)}",
                        'latitude': latitude,
                        'longitude': longitude,
                        'time': file_time,
                        'depth_min': depth_min,
                        'depth_max': depth_max,
                        'temperature_avg': temperature_avg,
                        'salinity_avg': salinity_avg,
                        'pressure_avg': pressure_avg
                    }
                    results.append(profile_data)
            except Exception:
                # Fallback to heuristic based on pre-extracted dictionary
                variables = data.get('variables', {})
                profile_data = {
                    'platform_number': platform_number,
                    'profile_id': f"{platform_number}_{os.path.basename(filepath)}",
                    'latitude': None,
                    'longitude': None,
                    'time': None,
                    'depth_min': None,
                    'depth_max': None,
                    'temperature_avg': None,
                    'salinity_avg': None,
                    'pressure_avg': None
                }
                for var_name, var_data in variables.items():
                    var_info = var_data.get('data')
                    if var_info is None:
                        continue
                    if 'lat' in var_name.lower() and var_info.size > 0:
                        profile_data['latitude'] = float(np.mean(var_info))
                    elif 'lon' in var_name.lower() and var_info.size > 0:
                        profile_data['longitude'] = float(np.mean(var_info))
                    elif 'time' in var_name.lower() and var_info.size > 0:
                        try:
                            profile_data['time'] = datetime.fromtimestamp(float(np.mean(var_info)))
                        except:
                            pass
                    elif 'temp' in var_name.lower() and var_info.size > 0:
                        profile_data['temperature_avg'] = float(np.mean(var_info))
                    elif 'sal' in var_name.lower() and var_info.size > 0:
                        profile_data['salinity_avg'] = float(np.mean(var_info))
                    elif 'pres' in var_name.lower() and var_info.size > 0:
                        profile_data['pressure_avg'] = float(np.mean(var_info))
                        profile_data['depth_min'] = float(np.min(var_info))
                        profile_data['depth_max'] = float(np.max(var_info))
                results.append(profile_data)
            
        except Exception as e:
            logger.error(f"Failed to process data file {filepath}: {e}")
        
        return results
    
    def process_realtime_file(self, data: Dict, platform_number: str, filepath: str) -> List[Dict]:
        """Process realtime NetCDF file (R prefix)"""
        # Similar to data file processing
        return self.process_data_file(data, platform_number, filepath)
    
    def insert_metadata(self, metadata_list: List[Dict]):
        """Insert metadata into database"""
        if not metadata_list:
            return
        
        try:
            cursor = self.connection.cursor()
            
            insert_sql = """
            INSERT INTO argo_metadata 
            (platform_number, latitude_min, latitude_max, longitude_min, longitude_max, 
             time_min, time_max, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for metadata in metadata_list:
                cursor.execute(insert_sql, (
                    metadata['platform_number'],
                    metadata['latitude_min'],
                    metadata['latitude_max'],
                    metadata['longitude_min'],
                    metadata['longitude_max'],
                    metadata['time_min'],
                    metadata['time_max'],
                    metadata['file_path']
                ))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Inserted {len(metadata_list)} metadata records")
            
        except Exception as e:
            logger.error(f"Failed to insert metadata: {e}")
            raise
    
    def insert_profiles(self, profiles_list: List[Dict]):
        """Insert profile data into database"""
        if not profiles_list:
            return
        
        try:
            cursor = self.connection.cursor()
            
            insert_sql = """
            INSERT INTO argo_profiles 
            (platform_number, profile_id, latitude, longitude, time, 
             depth_min, depth_max, temperature_avg, salinity_avg, pressure_avg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for profile in profiles_list:
                cursor.execute(insert_sql, (
                    profile['platform_number'],
                    profile['profile_id'],
                    profile['latitude'],
                    profile['longitude'],
                    profile['time'],
                    profile['depth_min'],
                    profile['depth_max'],
                    profile['temperature_avg'],
                    profile['salinity_avg'],
                    profile['pressure_avg']
                ))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Inserted {len(profiles_list)} profile records")
            
        except Exception as e:
            logger.error(f"Failed to insert profiles: {e}")
            raise
    
    def convert_all_files(self, argo_data_dir: str):
        """Convert all NetCDF files in directory to PostgreSQL"""
        try:
            self.connect_db()
            self.create_tables()
            
            # Get all NetCDF files
            netcdf_files = []
            for root, dirs, files in os.walk(argo_data_dir):
                for file in files:
                    if file.endswith('.nc'):
                        netcdf_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(netcdf_files)} NetCDF files to process")
            
            metadata_list = []
            profiles_list = []
            
            for filepath in netcdf_files:
                logger.info(f"Processing {filepath}")
                results = self.process_argo_file(filepath)
                
                for result in results:
                    if 'file_path' in result:  # Metadata
                        metadata_list.append(result)
                    else:  # Profile data
                        profiles_list.append(result)
            
            # Insert data into database
            if metadata_list:
                self.insert_metadata(metadata_list)
            
            if profiles_list:
                self.insert_profiles(profiles_list)
            
            logger.info("NetCDF to PostgreSQL conversion completed successfully")
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise
        finally:
            self.close_db()

def main():
    """Main function to run the conversion"""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'argo_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    # Create converter instance
    converter = NetCDFToPostgreSQL(db_config)
    
    # Convert all files
    argo_data_dir = 'argo_data'
    converter.convert_all_files(argo_data_dir)

if __name__ == "__main__":
    main()
