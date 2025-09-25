#!/usr/bin/env python3
"""
SQL Query Generator for LLM
Generates SQL queries based on natural language questions about ARGO data
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from src.utils.logging import get_logger

logger = get_logger(__name__)

class SQLQueryGenerator:
    """Generate SQL queries from natural language questions about ARGO data"""
    
    def __init__(self):
        self.schema_info = {
            'argo_metadata': {
                'columns': {
                    'platform_number': 'VARCHAR(20) - ARGO float identifier',
                    'latitude_min': 'DECIMAL(10,6) - Minimum latitude',
                    'latitude_max': 'DECIMAL(10,6) - Maximum latitude', 
                    'longitude_min': 'DECIMAL(10,6) - Minimum longitude',
                    'longitude_max': 'DECIMAL(10,6) - Maximum longitude',
                    'time_min': 'TIMESTAMP - Start time of data collection',
                    'time_max': 'TIMESTAMP - End time of data collection'
                },
                'description': 'Metadata about ARGO floats including location and time ranges'
            },
            'argo_profiles': {
                'columns': {
                    'platform_number': 'VARCHAR(20) - ARGO float identifier',
                    'profile_id': 'VARCHAR(50) - Unique profile identifier',
                    'latitude': 'DECIMAL(10,6) - Profile latitude',
                    'longitude': 'DECIMAL(10,6) - Profile longitude',
                    'time': 'TIMESTAMP - Profile collection time',
                    'depth_min': 'DECIMAL(8,2) - Minimum depth in meters',
                    'depth_max': 'DECIMAL(8,2) - Maximum depth in meters',
                    'temperature_avg': 'DECIMAL(8,3) - Average temperature in Celsius',
                    'salinity_avg': 'DECIMAL(8,3) - Average salinity in PSU',
                    'pressure_avg': 'DECIMAL(8,2) - Average pressure in dbar'
                },
                'description': 'Profile data from ARGO floats with averaged measurements'
            },
            'argo_measurements': {
                'columns': {
                    'platform_number': 'VARCHAR(20) - ARGO float identifier',
                    'profile_id': 'VARCHAR(50) - Profile identifier',
                    'latitude': 'DECIMAL(10,6) - Measurement latitude',
                    'longitude': 'DECIMAL(10,6) - Measurement longitude',
                    'time': 'TIMESTAMP - Measurement time',
                    'depth': 'DECIMAL(8,2) - Depth in meters',
                    'pressure': 'DECIMAL(8,2) - Pressure in dbar',
                    'temperature': 'DECIMAL(8,3) - Temperature in Celsius',
                    'salinity': 'DECIMAL(8,3) - Salinity in PSU',
                    'quality_flag': 'INTEGER - Data quality flag'
                },
                'description': 'Individual measurements from ARGO floats'
            }
        }
    
    def generate_sql_query(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        try:
            # Analyze the question to determine query type
            query_type = self._analyze_question_type(question)
            
            # Extract parameters from question
            params = self._extract_parameters(question, context)
            
            # Generate appropriate SQL query
            if query_type == 'location_based':
                sql = self._generate_location_query(question, params)
            elif query_type == 'temporal':
                sql = self._generate_temporal_query(question, params)
            elif query_type == 'comparative':
                sql = self._generate_comparative_query(question, params)
            elif query_type == 'statistical':
                sql = self._generate_statistical_query(question, params)
            elif query_type == 'nearest_floats':
                sql = self._generate_nearest_floats_query(question, params)
            else:
                sql = self._generate_general_query(question, params)

            # Constrain by nearest platform_numbers from context if provided
            platform_ids = (context or {}).get('nearest_platforms')
            if platform_ids:
                placeholders = ','.join([f"'{str(p)}'" for p in platform_ids])
                where_clause = f"platform_number IN ({placeholders})"

                def _inject_where(original_sql: str, clause: str) -> str:
                    s = original_sql.strip()
                    # Remove trailing semicolon
                    has_semicolon = s.endswith(';')
                    if has_semicolon:
                        s = s[:-1]

                    # Find ORDER BY or LIMIT to insert before
                    pattern = re.compile(r"\bORDER\s+BY\b|\bLIMIT\b", re.IGNORECASE)
                    m = pattern.search(s)
                    insert_pos = m.start() if m else len(s)

                    upper_s = s.upper()
                    where_pos = upper_s.find(' WHERE ')
                    if 0 <= where_pos < insert_pos:
                        # Append AND before ORDER/LIMIT
                        before = s[:insert_pos].rstrip()
                        after = s[insert_pos:]
                        # If WHERE is present but no condition yet at the end
                        if before.strip().upper().endswith('WHERE'):
                            before = before + ' ' + clause
                        else:
                            before = before + ' AND ' + clause
                        s = before + after
                    else:
                        # Insert WHERE before ORDER/LIMIT
                        before = s[:insert_pos].rstrip()
                        after = s[insert_pos:]
                        before = before + ' WHERE ' + clause
                        s = before + after

                    return s + (';' if has_semicolon else '')

                sql = _inject_where(sql, where_clause)
            
            return {
                'sql': sql,
                'query_type': query_type,
                'parameters': params,
                'explanation': self._explain_query(sql, question)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate SQL query: {e}")
            return {
                'sql': None,
                'error': str(e),
                'fallback': True
            }
    
    def _analyze_question_type(self, question: str) -> str:
        """Analyze question to determine query type"""
        question_lower = question.lower()
        
        # Location-based queries
        if any(word in question_lower for word in ['near', 'closest', 'nearest', 'location', 'coordinates', 'lat', 'lon']):
            return 'location_based'
        
        # Temporal queries
        if any(word in question_lower for word in ['time', 'date', 'when', 'recent', 'latest', 'oldest', 'year', 'month', 'day']):
            return 'temporal'
        
        # Comparative queries
        if any(word in question_lower for word in ['compare', 'difference', 'between', 'versus', 'vs', 'contrast']):
            return 'comparative'
        
        # Statistical queries
        if any(word in question_lower for word in ['average', 'mean', 'max', 'min', 'maximum', 'minimum', 'statistics', 'stats']):
            return 'statistical'
        
        # Nearest floats queries
        if any(word in question_lower for word in ['nearest', 'closest', 'nearby']):
            return 'nearest_floats'
        
        return 'general'
    
    def _extract_parameters(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract parameters from question and context"""
        params = {}
        
        # Extract coordinates if provided in context
        if context:
            if 'lat' in context and 'lon' in context:
                params['latitude'] = float(context['lat'])
                params['longitude'] = float(context['lon'])
        
        # Extract coordinates from question text
        lat_match = re.search(r'lat[itude]*\s*:?\s*([+-]?\d+\.?\d*)', question, re.IGNORECASE)
        lon_match = re.search(r'lon[gitude]*\s*:?\s*([+-]?\d+\.?\d*)', question, re.IGNORECASE)
        
        if lat_match:
            params['latitude'] = float(lat_match.group(1))
        if lon_match:
            params['longitude'] = float(lon_match.group(1))
        
        # Extract time parameters
        time_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', question)
        if time_match:
            year, month, day = time_match.groups()
            params['date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extract depth parameters
        depth_match = re.search(r'depth\s*:?\s*(\d+)', question, re.IGNORECASE)
        if depth_match:
            params['depth'] = float(depth_match.group(1))
        
        # Extract platform numbers
        platform_match = re.search(r'float\s*:?\s*(\d+)', question, re.IGNORECASE)
        if platform_match:
            params['platform_number'] = platform_match.group(1)
        
        return params
    
    def _generate_location_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate location-based SQL query"""
        if 'latitude' in params and 'longitude' in params:
            lat = params['latitude']
            lon = params['longitude']
            
            # Find nearest floats using haversine distance
            sql = f"""
            WITH distances AS (
                SELECT 
                    platform_number,
                    latitude,
                    longitude,
                    time,
                    temperature_avg,
                    salinity_avg,
                    depth_min,
                    depth_max,
                    ST_Distance(
                        ST_Point({lon}, {lat})::geography,
                        ST_Point(longitude, latitude)::geography
                    ) as distance_meters
                FROM argo_profiles
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            )
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max,
                ROUND(distance_meters/1000, 2) as distance_km
            FROM distances
            ORDER BY distance_meters
            LIMIT 5;
            """
        else:
            # General location query
            sql = """
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max
            FROM argo_profiles
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY time DESC
            LIMIT 20;
            """
        
        return sql
    
    def _generate_temporal_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate temporal SQL query"""
        if 'date' in params:
            date = params['date']
            sql = f"""
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max
            FROM argo_profiles
            WHERE DATE(time) = '{date}'
            ORDER BY time DESC;
            """
        else:
            # Recent data query
            sql = """
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max
            FROM argo_profiles
            WHERE time >= NOW() - INTERVAL '30 days'
            ORDER BY time DESC
            LIMIT 50;
            """
        
        return sql
    
    def _generate_comparative_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate comparative SQL query"""
        sql = """
        SELECT 
            platform_number,
            latitude,
            longitude,
            time,
            temperature_avg,
            salinity_avg,
            depth_min,
            depth_max,
            COUNT(*) OVER() as total_profiles
        FROM argo_profiles
        WHERE temperature_avg IS NOT NULL 
        AND salinity_avg IS NOT NULL
        ORDER BY time DESC
        LIMIT 20;
        """
        return sql
    
    def _generate_statistical_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate statistical SQL query"""
        sql = """
        SELECT 
            COUNT(*) as total_profiles,
            AVG(temperature_avg) as avg_temperature,
            MIN(temperature_avg) as min_temperature,
            MAX(temperature_avg) as max_temperature,
            AVG(salinity_avg) as avg_salinity,
            MIN(salinity_avg) as min_salinity,
            MAX(salinity_avg) as max_salinity,
            AVG(depth_max - depth_min) as avg_depth_range
        FROM argo_profiles
        WHERE temperature_avg IS NOT NULL 
        AND salinity_avg IS NOT NULL;
        """
        return sql
    
    def _generate_nearest_floats_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate query to find nearest floats"""
        if 'latitude' in params and 'longitude' in params:
            lat = params['latitude']
            lon = params['longitude']
            
            sql = f"""
            WITH distances AS (
                SELECT 
                    platform_number,
                    latitude,
                    longitude,
                    time,
                    temperature_avg,
                    salinity_avg,
                    depth_min,
                    depth_max,
                    ST_Distance(
                        ST_Point({lon}, {lat})::geography,
                        ST_Point(longitude, latitude)::geography
                    ) as distance_meters
                FROM argo_profiles
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            )
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max,
                ROUND(distance_meters/1000, 2) as distance_km
            FROM distances
            ORDER BY distance_meters
            LIMIT 2;
            """
        else:
            sql = """
            SELECT 
                platform_number,
                latitude,
                longitude,
                time,
                temperature_avg,
                salinity_avg,
                depth_min,
                depth_max
            FROM argo_profiles
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY time DESC
            LIMIT 2;
            """
        
        return sql
    
    def _generate_general_query(self, question: str, params: Dict[str, Any]) -> str:
        """Generate general SQL query"""
        sql = """
        SELECT 
            platform_number,
            latitude,
            longitude,
            time,
            temperature_avg,
            salinity_avg,
            depth_min,
            depth_max
        FROM argo_profiles
        WHERE temperature_avg IS NOT NULL 
        AND salinity_avg IS NOT NULL
        ORDER BY time DESC
        LIMIT 20;
        """
        return sql
    
    def _explain_query(self, sql: str, question: str) -> str:
        """Generate explanation for the SQL query"""
        explanation = f"""
        This SQL query was generated to answer: "{question}"
        
        The query retrieves ARGO float data from the database, including:
        - Platform number (float identifier)
        - Geographic coordinates (latitude, longitude)
        - Time of measurement
        - Oceanographic parameters (temperature, salinity)
        - Depth information
        
        The results are ordered by relevance and limited to provide focused answers.
        """
        return explanation
    
    def get_schema_info(self) -> str:
        """Get database schema information for LLM context"""
        schema_info = "ARGO Database Schema:\n\n"
        
        for table_name, table_info in self.schema_info.items():
            schema_info += f"Table: {table_name}\n"
            schema_info += f"Description: {table_info['description']}\n"
            schema_info += "Columns:\n"
            
            for col_name, col_info in table_info['columns'].items():
                schema_info += f"  - {col_name}: {col_info}\n"
            
            schema_info += "\n"
        
        return schema_info

def main():
    """Test the SQL query generator"""
    generator = SQLQueryGenerator()
    
    # Test questions
    test_questions = [
        "What are the nearest ARGO floats to latitude 10.5, longitude 75.2?",
        "Show me temperature data from the last month",
        "Compare salinity between different floats",
        "What is the average temperature in the Indian Ocean?",
        "Find floats near my location"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        result = generator.generate_sql_query(question)
        print(f"SQL: {result['sql']}")
        print(f"Type: {result['query_type']}")

if __name__ == "__main__":
    main()
