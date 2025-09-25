#!/usr/bin/env python3
"""
SQL-Enhanced RAG Pipeline
Uses SQL queries to retrieve precise data for LLM responses
"""

import os
import sys
import json
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.llm.sql_query_generator import SQLQueryGenerator
from src.llm.models import get_llm, get_hf_router_client, hf_chat_complete
from src.utils.logging import get_logger

logger = get_logger(__name__)

class SQLRAGPipeline:
    """Enhanced RAG pipeline using SQL queries for precise data retrieval"""
    
    def __init__(self, db_config: Dict[str, str] | None):
        self.db_config = db_config
        self.sql_generator = SQLQueryGenerator()
        self.connection = None
        
    def connect_db(self):
        """Connect to SQLite database"""
        try:
            db_path = str(Path("data") / "argo.db")
            self.connection = sqlite3.connect(db_path)
            logger.info("Connected to SQLite database: %s", db_path)
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def close_db(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def execute_sql_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            if not self.connection:
                self.connect_db()

            cursor = self.connection.cursor()
            cursor.execute(sql)

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch results
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = []
            for row in rows:
                result_dict = {}
                for i, value in enumerate(row):
                    result_dict[columns[i]] = value
                results.append(result_dict)

            cursor.close()
            logger.info(f"Executed SQL query, returned {len(results)} rows")
            return results
        except Exception as e:
            logger.error(f"Failed to execute SQL query: {e}")
            return []

    def get_variable_availability(self, platform_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Return per-platform variable availability and semantic types.

        Availability is inferred from non-null counts in argo_profiles columns.
        """
        availability: Dict[str, Dict[str, Any]] = {}
        if not platform_ids:
            return availability

        # For SQLite per-float tables, approximate availability by checking non-null counts per table
        try:
            if not platform_ids:
                return {}
            if not self.connection:
                self.connect_db()
            cursor = self.connection.cursor()
            for pid in platform_ids:
                table = f"float_{pid}"
                try:
                    cursor.execute(
                        f"SELECT COUNT(*), COUNT(temperature_avg), COUNT(salinity_avg), COUNT(pressure_avg), COUNT(depth_min), COUNT(depth_max) FROM {table}"
                    )
                    total, has_temp, has_sal, has_pres, has_dmin, has_dmax = cursor.fetchone()
                    vars_available = []
                    if has_temp > 0:
                        vars_available.append("TEMP")
                    if has_sal > 0:
                        vars_available.append("PSAL")
                    if has_pres > 0:
                        vars_available.append("PRES")
                    if has_dmin > 0 or has_dmax > 0:
                        vars_available.append("DEPTH")
                    availability[str(pid)] = {
                        "available_vars": vars_available,
                        "types": {
                            "TEMP": "float (°C)",
                            "PSAL": "float (PSU)",
                            "PRES": "float (dbar)",
                            "DEPTH": "float (m)",
                            "LATITUDE": "float (deg)",
                            "LONGITUDE": "float (deg)",
                            "TIME": "timestamp",
                        },
                        "total_rows": int(total),
                    }
                except Exception:
                    continue
            cursor.close()
        except Exception:
            return {}

        return availability
    
    def format_data_for_llm(self, data: List[Dict[str, Any]], query_type: str) -> str:
        """Format retrieved data for LLM consumption"""
        if not data:
            return "No data found matching the query criteria."
        
        formatted_data = f"Retrieved {len(data)} records:\n\n"
        
        if query_type == 'location_based':
            formatted_data += "Nearest ARGO Floats:\n"
            for i, record in enumerate(data[:5], 1):
                formatted_data += f"{i}. Float {record.get('platform_number', 'N/A')}\n"
                formatted_data += f"   Location: {record.get('latitude', 'N/A')}°N, {record.get('longitude', 'N/A')}°E\n"
                formatted_data += f"   Time: {record.get('time', 'N/A')}\n"
                formatted_data += f"   Temperature: {record.get('temperature_avg', 'N/A')}°C\n"
                formatted_data += f"   Salinity: {record.get('salinity_avg', 'N/A')} PSU\n"
                if 'distance_km' in record:
                    formatted_data += f"   Distance: {record.get('distance_km', 'N/A')} km\n"
                formatted_data += "\n"
        
        elif query_type == 'statistical':
            if data:
                record = data[0]
                formatted_data += "Statistical Summary:\n"
                formatted_data += f"Total Profiles: {record.get('total_profiles', 'N/A')}\n"
                formatted_data += f"Average Temperature: {record.get('avg_temperature', 'N/A')}°C\n"
                formatted_data += f"Temperature Range: {record.get('min_temperature', 'N/A')}°C to {record.get('max_temperature', 'N/A')}°C\n"
                formatted_data += f"Average Salinity: {record.get('avg_salinity', 'N/A')} PSU\n"
                formatted_data += f"Salinity Range: {record.get('min_salinity', 'N/A')} PSU to {record.get('max_salinity', 'N/A')} PSU\n"
                formatted_data += f"Average Depth Range: {record.get('avg_depth_range', 'N/A')} m\n"
        
        elif query_type == 'temporal':
            formatted_data += "Temporal Data:\n"
            for i, record in enumerate(data[:10], 1):
                formatted_data += f"{i}. Float {record.get('platform_number', 'N/A')} - {record.get('time', 'N/A')}\n"
                formatted_data += f"   Location: {record.get('latitude', 'N/A')}°N, {record.get('longitude', 'N/A')}°E\n"
                formatted_data += f"   Temperature: {record.get('temperature_avg', 'N/A')}°C\n"
                formatted_data += f"   Salinity: {record.get('salinity_avg', 'N/A')} PSU\n\n"
        
        else:
            # General formatting
            formatted_data += "ARGO Float Data:\n"
            for i, record in enumerate(data[:10], 1):
                formatted_data += f"{i}. Float {record.get('platform_number', 'N/A')}\n"
                formatted_data += f"   Location: {record.get('latitude', 'N/A')}°N, {record.get('longitude', 'N/A')}°E\n"
                formatted_data += f"   Time: {record.get('time', 'N/A')}\n"
                formatted_data += f"   Temperature: {record.get('temperature_avg', 'N/A')}°C\n"
                formatted_data += f"   Salinity: {record.get('salinity_avg', 'N/A')} PSU\n"
                formatted_data += f"   Depth Range: {record.get('depth_min', 'N/A')}m - {record.get('depth_max', 'N/A')}m\n\n"
        
        return formatted_data
    
    def generate_response(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate LLM response using SQL-enhanced RAG and return structured output."""
        try:
            # Generate SQL query from question
            query_result = self.sql_generator.generate_sql_query(question, context)
            
            if query_result.get('error'):
                logger.error(f"SQL generation failed: {query_result['error']}")
                return {
                    "answer": "I'm sorry, I couldn't process your question at the moment. Please try again.",
                    "sql": None,
                    "data": [],
                    "query_type": None,
                    "nearest_platforms": (context or {}).get("nearest_platforms", []),
                }
            
            sql = query_result['sql']
            query_type = query_result['query_type']
            
            if not sql:
                return {
                    "answer": "I couldn't generate a suitable query for your question. Please try rephrasing it.",
                    "sql": None,
                    "data": [],
                    "query_type": query_type,
                    "nearest_platforms": (context or {}).get("nearest_platforms", []),
                }
            
            # Execute SQL query
            data = self.execute_sql_query(sql)
            
            # Format data for LLM
            formatted_data = self.format_data_for_llm(data, query_type)
            
            # Create enhanced prompt with data
            schema_info = self.sql_generator.get_schema_info()
            nearest_platforms = (context or {}).get("nearest_platforms", [])
            var_availability = self.get_variable_availability(nearest_platforms) if nearest_platforms else {}
            availability_text = "\n".join(
                [
                    f"- Platform {pid}: vars={','.join(info.get('available_vars', []))} rows={info.get('total_rows', 0)}"
                    for pid, info in var_availability.items()
                ]
            ) or "- (no availability info)"
            
            # Optionally include precomputed variable catalog if provided in context
            catalog_text = ""
            catalog = (context or {}).get("variable_catalog")
            if catalog:
                try:
                    # Expecting a small dict with tables->columns and types
                    preview = json.dumps(catalog.get("tables", {}), indent=2)[:1200]
                    catalog_text = f"\nVariable Catalog (schema/types):\n```\n{preview}\n```\n"
                except Exception:
                    catalog_text = ""

            prompt = f"""
            You are an expert oceanographer and ARGO data analyst. Answer the user's question based on the retrieved data.
            
            Database Schema:
            {schema_info}
            
            Variable Availability (for nearest platforms):
            {availability_text}

            {catalog_text}

            User Question: {question}
            
            Retrieved Data:
            {formatted_data}
            
            Instructions:
            1. Provide a clear, accurate answer based on the retrieved data
            2. If the data shows specific values, mention them
            3. Explain what the data means in oceanographic terms
            4. If comparing data, highlight key differences
            5. Use appropriate scientific language but keep it accessible
            6. If no data was found, explain what might be the reason
            
            Answer:
            """
            
            # Get LLM response
            client = get_hf_router_client()
            if client is not None:
                response = hf_chat_complete(client, model="openai/gpt-oss-20b", prompt=prompt)
            else:
                llm = get_llm(model_type="openrouter")
                try:
                    resp = llm.invoke(prompt)
                    response = getattr(resp, "content", str(resp))
                except Exception:
                    try:
                        response = llm.predict(prompt)
                    except Exception:
                        try:
                            response = llm(prompt)
                        except Exception:
                            response = "I'm sorry, I couldn't generate a response at the moment."

            return {
                "answer": response,
                "sql": sql,
                "data": data,
                "query_type": query_type,
                "nearest_platforms": (context or {}).get("nearest_platforms", []),
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "sql": None,
                "data": [],
                "query_type": None,
                "nearest_platforms": (context or {}).get("nearest_platforms", []),
            }
    
    def get_nearest_floats(self, latitude: float, longitude: float, limit: int = 2) -> List[Dict[str, Any]]:
        """Get nearest ARGO floats to given coordinates"""
        try:
            # Nearest computation handled outside via Chroma; for SQLite we return latest per platform
            return []
            
        except Exception as e:
            logger.error(f"Failed to get nearest floats: {e}")
            return []
    
    def get_comparative_analysis(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get comparative analysis of nearest floats"""
        try:
            floats = self.get_nearest_floats(latitude, longitude, 2)
            
            if len(floats) < 2:
                return {
                    'analysis': 'Not enough nearby floats for comparison.',
                    'floats': floats
                }
            
            # Generate comparative analysis
            float1, float2 = floats[0], floats[1]
            
            analysis_prompt = f"""
            Compare these two ARGO floats and provide insights:
            
            Float 1 (Closest):
            - ID: {float1.get('platform_number', 'N/A')}
            - Location: {float1.get('latitude', 'N/A')}°N, {float1.get('longitude', 'N/A')}°E
            - Distance: {float1.get('distance_km', 'N/A')} km
            - Temperature: {float1.get('temperature_avg', 'N/A')}°C
            - Salinity: {float1.get('salinity_avg', 'N/A')} PSU
            - Depth Range: {float1.get('depth_min', 'N/A')} - {float1.get('depth_max', 'N/A')} m
            
            Float 2 (Second Closest):
            - ID: {float2.get('platform_number', 'N/A')}
            - Location: {float2.get('latitude', 'N/A')}°N, {float2.get('longitude', 'N/A')}°E
            - Distance: {float2.get('distance_km', 'N/A')} km
            - Temperature: {float2.get('temperature_avg', 'N/A')}°C
            - Salinity: {float2.get('salinity_avg', 'N/A')} PSU
            - Depth Range: {float2.get('depth_min', 'N/A')} - {float2.get('depth_max', 'N/A')} m
            
            Provide a comparative analysis highlighting:
            1. Key differences between the floats
            2. What these differences indicate about ocean conditions
            3. Implications for the user's location
            4. Scientific significance of the data
            """
            
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
                'analysis': analysis,
                'floats': floats
            }
            
        except Exception as e:
            logger.error(f"Failed to get comparative analysis: {e}")
            return {
                'analysis': 'Unable to perform analysis at the moment.',
                'floats': []
            }

def main():
    """Test the SQL RAG pipeline"""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'argo_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    # Create pipeline
    pipeline = SQLRAGPipeline(db_config)
    
    # Test questions
    test_questions = [
        "What are the nearest ARGO floats to latitude 10.5, longitude 75.2?",
        "Show me the latest temperature data",
        "Compare salinity between different floats"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        response = pipeline.generate_response(question)
        print(f"Response: {response}")

if __name__ == "__main__":
    main()
