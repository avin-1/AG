#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for ARGO Data
Creates database, tables, and converts NetCDF files
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.netcdf_to_postgres import NetCDFToPostgreSQL
from src.utils.logging import get_logger

logger = get_logger(__name__)

def create_database():
    """Create PostgreSQL database for ARGO data"""
    # Connect to default postgres database
    conn = psycopg2.connect(
        host='localhost',
        database='postgres',
        user='postgres',
        password='password',
        port=5432
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    try:
        # Create database
        cursor.execute("CREATE DATABASE argo_db;")
        logger.info("Database 'argo_db' created successfully")
    except psycopg2.errors.DuplicateDatabase:
        logger.info("Database 'argo_db' already exists")
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def setup_postgres_extension():
    """Setup PostGIS extension for spatial queries"""
    db_config = {
        'host': 'localhost',
        'database': 'argo_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Enable PostGIS extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        logger.info("PostGIS extension enabled")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"PostGIS extension not available: {e}")
        logger.info("Continuing without spatial extensions...")

def convert_netcdf_files():
    """Convert NetCDF files to PostgreSQL"""
    db_config = {
        'host': 'localhost',
        'database': 'argo_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    # Create converter
    converter = NetCDFToPostgreSQL(db_config)
    
    # Convert all NetCDF files
    argo_data_dir = 'argo_data'
    converter.convert_all_files(argo_data_dir)

def main():
    """Main setup function"""
    try:
        logger.info("Starting PostgreSQL database setup...")
        
        # Create database
        create_database()
        
        # Setup PostGIS extension
        setup_postgres_extension()
        
        # Convert NetCDF files
        logger.info("Converting NetCDF files to PostgreSQL...")
        convert_netcdf_files()
        
        logger.info("PostgreSQL database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
