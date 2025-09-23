# FloatChat - Low-Level Design (LLD) Document - MCP Approach

## Document Information
- **Project**: FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data Discovery
- **Version**: 1.0
- **Date**: September 2024
- **Approach**: Model Context Protocol (MCP)
- **Organization**: Ministry of Earth Sciences (MoES) - INCOIS

## 1. Overview

This document provides detailed technical specifications for the FloatChat MCP implementation, including tool specifications, protocol details, database schemas, and implementation code.

## 2. MCP Protocol Implementation

### 2.1 MCP Server Core

#### 2.1.1 MCP Server (`src/mcp/server.py`)
```python
import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class MCPMessageType(Enum):
    """MCP message types"""
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    CONTEXT_UPDATE = "context/update"
    ERROR = "error"

@dataclass
class MCPMessage:
    """MCP message structure"""
    type: MCPMessageType
    id: str
    data: Dict[str, Any]
    timestamp: float

class MCPFloatChatServer:
    """Main MCP server implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.tools = self._register_tools()
        self.context_manager = ContextManager()
        self.resource_manager = ResourceManager()
        self.sessions = {}
    
    def _register_tools(self) -> Dict[str, 'MCPTool']:
        """Register all available MCP tools"""
        return {
            "query_argo_database": ArgoQueryTool(),
            "get_float_metadata": ArgoMetadataTool(),
            "search_by_location": ArgoGeographicTool(),
            "generate_plot": ArgoVisualizationTool(),
            "export_data": ArgoExportTool(),
            "get_data_statistics": ArgoStatisticsTool()
        }
    
    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP messages"""
        try:
            if message.type == MCPMessageType.INITIALIZE:
                return await self._handle_initialize(message)
            elif message.type == MCPMessageType.TOOLS_LIST:
                return await self._handle_tools_list(message)
            elif message.type == MCPMessageType.TOOLS_CALL:
                return await self._handle_tool_call(message)
            elif message.type == MCPMessageType.CONTEXT_UPDATE:
                return await self._handle_context_update(message)
            else:
                return self._create_error_message(message.id, "Unknown message type")
        except Exception as e:
            return self._create_error_message(message.id, str(e))
    
    async def _handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """Handle initialization request"""
        session_id = message.data.get("session_id")
        if not session_id:
            session_id = self._generate_session_id()
        
        self.sessions[session_id] = {
            "created_at": message.timestamp,
            "context": {},
            "tool_calls": []
        }
        
        return MCPMessage(
            type=MCPMessageType.INITIALIZE,
            id=message.id,
            data={
                "session_id": session_id,
                "server_capabilities": {
                    "tools": list(self.tools.keys()),
                    "context_management": True,
                    "resource_management": True
                }
            },
            timestamp=asyncio.get_event_loop().time()
        )
    
    async def _handle_tools_list(self, message: MCPMessage) -> MCPMessage:
        """Handle tools list request"""
        tools_spec = []
        for tool_name, tool in self.tools.items():
            tools_spec.append(tool.get_specification())
        
        return MCPMessage(
            type=MCPMessageType.TOOLS_LIST,
            id=message.id,
            data={"tools": tools_spec},
            timestamp=asyncio.get_event_loop().time()
        )
    
    async def _handle_tool_call(self, message: MCPMessage) -> MCPMessage:
        """Handle tool execution request"""
        tool_name = message.data.get("tool_name")
        parameters = message.data.get("parameters", {})
        session_id = message.data.get("session_id")
        
        if tool_name not in self.tools:
            return self._create_error_message(message.id, f"Tool '{tool_name}' not found")
        
        # Get tool and execute
        tool = self.tools[tool_name]
        context = self.sessions.get(session_id, {}).get("context", {})
        
        try:
            result = await tool.execute(parameters, context)
            
            # Update session context
            if session_id in self.sessions:
                self.sessions[session_id]["tool_calls"].append({
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "timestamp": message.timestamp
                })
            
            return MCPMessage(
                type=MCPMessageType.TOOLS_CALL,
                id=message.id,
                data={
                    "tool_name": tool_name,
                    "result": result,
                    "execution_time": asyncio.get_event_loop().time() - message.timestamp
                },
                timestamp=asyncio.get_event_loop().time()
            )
        except Exception as e:
            return self._create_error_message(message.id, f"Tool execution error: {str(e)}")
    
    def _create_error_message(self, message_id: str, error: str) -> MCPMessage:
        """Create error message"""
        return MCPMessage(
            type=MCPMessageType.ERROR,
            id=message_id,
            data={"error": error},
            timestamp=asyncio.get_event_loop().time()
        )
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())
```

### 2.2 MCP Tool Base Class

#### 2.2.1 Base Tool (`src/mcp/tools/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json

class MCPTool(ABC):
    """Base class for MCP tools"""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.input_schema = self.get_input_schema()
    
    @abstractmethod
    def get_name(self) -> str:
        """Get tool name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get tool description"""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for tool"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with given parameters and context"""
        pass
    
    def get_specification(self) -> Dict[str, Any]:
        """Get complete tool specification"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters against schema"""
        # Basic validation - can be enhanced with JSON Schema
        required_fields = self.input_schema.get("required", [])
        for field in required_fields:
            if field not in parameters:
                raise ValueError(f"Required parameter '{field}' missing")
        return True
```

### 2.3 ARGO Database Tools

#### 2.3.1 Query Tool (`src/mcp/tools/argo_query.py`)
```python
import asyncio
import psycopg2
from typing import Dict, Any, List
from src.mcp.tools.base import MCPTool
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ArgoQueryTool(MCPTool):
    """Tool for executing SQL queries on ARGO database"""
    
    def get_name(self) -> str:
        return "query_argo_database"
    
    def get_description(self) -> str:
        return "Execute SQL queries on ARGO float database with security validation"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "SQL query to execute on ARGO database"
                },
                "parameters": {
                    "type": "object",
                    "description": "Query parameters for prepared statements",
                    "additionalProperties": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return",
                    "default": 1000
                }
            },
            "required": ["sql_query"]
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query with security validation"""
        self.validate_parameters(parameters)
        
        sql_query = parameters["sql_query"]
        query_params = parameters.get("parameters", {})
        limit = parameters.get("limit", 1000)
        
        # Security validation
        if not self._validate_sql_query(sql_query):
            raise ValueError("SQL query failed security validation")
        
        try:
            # Execute query
            results = await self._execute_query(sql_query, query_params, limit)
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results),
                "query": sql_query,
                "execution_time": asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": sql_query
            }
    
    def _validate_sql_query(self, sql_query: str) -> bool:
        """Validate SQL query for security"""
        sql_upper = sql_query.upper()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"Dangerous keyword '{keyword}' found in query")
                return False
        
        # Check for allowed tables
        allowed_tables = ['argo_floats', 'argo_profiles', 'tool_executions']
        for table in allowed_tables:
            if table in sql_upper:
                return True
        
        logger.warning("No allowed tables found in query")
        return False
    
    async def _execute_query(self, sql_query: str, params: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Execute SQL query with connection pooling"""
        # Add LIMIT if not present
        if 'LIMIT' not in sql_query.upper():
            sql_query += f" LIMIT {limit}"
        
        # Database connection (simplified - should use connection pool)
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="floatchat",
            user="postgres",
            password="3303"
        )
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query, params)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            return results
        finally:
            conn.close()
```

#### 2.3.2 Metadata Tool (`src/mcp/tools/argo_metadata.py`)
```python
import pandas as pd
from typing import Dict, Any, List
from src.mcp.tools.base import MCPTool
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ArgoMetadataTool(MCPTool):
    """Tool for retrieving ARGO float metadata"""
    
    def get_name(self) -> str:
        return "get_float_metadata"
    
    def get_description(self) -> str:
        return "Get metadata for ARGO floats including location, time ranges, and statistics"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "platform_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of platform numbers to get metadata for"
                },
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "format": "date"},
                        "end": {"type": "string", "format": "date"}
                    },
                    "description": "Date range filter"
                },
                "region": {
                    "type": "string",
                    "description": "Geographic region filter (e.g., 'Arabian Sea', 'Bay of Bengal')"
                },
                "include_statistics": {
                    "type": "boolean",
                    "description": "Include statistical summaries",
                    "default": True
                }
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve ARGO float metadata"""
        self.validate_parameters(parameters)
        
        try:
            # Load metadata
            metadata_df = pd.read_csv("data/processed/metadata.csv")
            
            # Apply filters
            filtered_df = self._apply_filters(metadata_df, parameters)
            
            # Convert to dictionary format
            results = []
            for _, row in filtered_df.iterrows():
                result = {
                    "platform_number": row["PLATFORM_NUMBER"],
                    "latitude_range": {
                        "min": float(row["LATITUDE_min"]),
                        "max": float(row["LATITUDE_max"])
                    },
                    "longitude_range": {
                        "min": float(row["LONGITUDE_min"]),
                        "max": float(row["LONGITUDE_max"])
                    },
                    "time_range": {
                        "start": str(row["TIME_min"]),
                        "end": str(row["TIME_max"])
                    }
                }
                results.append(result)
            
            # Add statistics if requested
            statistics = {}
            if parameters.get("include_statistics", True):
                statistics = self._calculate_statistics(filtered_df)
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "statistics": statistics
            }
        except Exception as e:
            logger.error(f"Metadata retrieval error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _apply_filters(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to metadata DataFrame"""
        filtered_df = df.copy()
        
        # Filter by platform numbers
        if "platform_numbers" in parameters:
            platform_numbers = parameters["platform_numbers"]
            filtered_df = filtered_df[filtered_df["PLATFORM_NUMBER"].isin(platform_numbers)]
        
        # Filter by date range
        if "date_range" in parameters:
            date_range = parameters["date_range"]
            if "start" in date_range:
                filtered_df = filtered_df[filtered_df["TIME_min"] >= date_range["start"]]
            if "end" in date_range:
                filtered_df = filtered_df[filtered_df["TIME_max"] <= date_range["end"]]
        
        # Filter by region (simplified)
        if "region" in parameters:
            region = parameters["region"].lower()
            if region == "arabian sea":
                filtered_df = filtered_df[
                    (filtered_df["LATITUDE_min"] >= 10) & 
                    (filtered_df["LATITUDE_max"] <= 25) &
                    (filtered_df["LONGITUDE_min"] >= 50) & 
                    (filtered_df["LONGITUDE_max"] <= 80)
                ]
            elif region == "bay of bengal":
                filtered_df = filtered_df[
                    (filtered_df["LATITUDE_min"] >= 5) & 
                    (filtered_df["LATITUDE_max"] <= 25) &
                    (filtered_df["LONGITUDE_min"] >= 80) & 
                    (filtered_df["LONGITUDE_max"] <= 100)
                ]
        
        return filtered_df
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics for filtered data"""
        if df.empty:
            return {}
        
        return {
            "total_floats": len(df),
            "latitude_range": {
                "min": float(df["LATITUDE_min"].min()),
                "max": float(df["LATITUDE_max"].max())
            },
            "longitude_range": {
                "min": float(df["LONGITUDE_min"].min()),
                "max": float(df["LONGITUDE_max"].max())
            },
            "time_range": {
                "start": str(df["TIME_min"].min()),
                "end": str(df["TIME_max"].max())
            }
        }
```

### 2.4 Geographic Search Tool

#### 2.4.1 Geographic Tool (`src/mcp/tools/argo_geographic.py`)
```python
import pandas as pd
from typing import Dict, Any, List
from src.mcp.tools.base import MCPTool
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ArgoGeographicTool(MCPTool):
    """Tool for geographic-based ARGO float searches"""
    
    def get_name(self) -> str:
        return "search_by_location"
    
    def get_description(self) -> str:
        return "Find ARGO floats by geographic criteria including regions, coordinates, and depth ranges"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Named region (e.g., 'Arabian Sea', 'Bay of Bengal', 'Indian Ocean')"
                },
                "bounds": {
                    "type": "object",
                    "properties": {
                        "north": {"type": "number"},
                        "south": {"type": "number"},
                        "east": {"type": "number"},
                        "west": {"type": "number"}
                    },
                    "description": "Geographic bounds (latitude/longitude)"
                },
                "center_point": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "radius_km": {"type": "number"}
                    },
                    "description": "Search within radius of center point"
                },
                "depth_range": {
                    "type": "object",
                    "properties": {
                        "min_depth": {"type": "number"},
                        "max_depth": {"type": "number"}
                    },
                    "description": "Depth range filter"
                }
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Search ARGO floats by geographic criteria"""
        try:
            # Load metadata
            metadata_df = pd.read_csv("data/processed/metadata.csv")
            
            # Apply geographic filters
            filtered_df = self._apply_geographic_filters(metadata_df, parameters)
            
            # Convert to results
            results = []
            for _, row in filtered_df.iterrows():
                result = {
                    "platform_number": row["PLATFORM_NUMBER"],
                    "location": {
                        "latitude_range": [float(row["LATITUDE_min"]), float(row["LATITUDE_max"])],
                        "longitude_range": [float(row["LONGITUDE_min"]), float(row["LONGITUDE_max"])]
                    },
                    "time_range": {
                        "start": str(row["TIME_min"]),
                        "end": str(row["TIME_max"])
                    },
                    "region": self._identify_region(row)
                }
                results.append(result)
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "search_criteria": parameters
            }
        except Exception as e:
            logger.error(f"Geographic search error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _apply_geographic_filters(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Apply geographic filters to DataFrame"""
        filtered_df = df.copy()
        
        # Filter by region
        if "region" in parameters:
            region_bounds = self._get_region_bounds(parameters["region"])
            if region_bounds:
                filtered_df = filtered_df[
                    (filtered_df["LATITUDE_min"] >= region_bounds["south"]) &
                    (filtered_df["LATITUDE_max"] <= region_bounds["north"]) &
                    (filtered_df["LONGITUDE_min"] >= region_bounds["west"]) &
                    (filtered_df["LONGITUDE_max"] <= region_bounds["east"])
                ]
        
        # Filter by bounds
        if "bounds" in parameters:
            bounds = parameters["bounds"]
            filtered_df = filtered_df[
                (filtered_df["LATITUDE_min"] >= bounds["south"]) &
                (filtered_df["LATITUDE_max"] <= bounds["north"]) &
                (filtered_df["LONGITUDE_min"] >= bounds["west"]) &
                (filtered_df["LONGITUDE_max"] <= bounds["east"])
            ]
        
        # Filter by center point and radius
        if "center_point" in parameters:
            center = parameters["center_point"]
            lat, lon = center["latitude"], center["longitude"]
            radius_km = center["radius_km"]
            
            # Simple distance calculation (can be enhanced)
            filtered_df = filtered_df[
                (filtered_df["LATITUDE_min"] >= lat - radius_km/111) &
                (filtered_df["LATITUDE_max"] <= lat + radius_km/111) &
                (filtered_df["LONGITUDE_min"] >= lon - radius_km/111) &
                (filtered_df["LONGITUDE_max"] <= lon + radius_km/111)
            ]
        
        return filtered_df
    
    def _get_region_bounds(self, region: str) -> Dict[str, float]:
        """Get geographic bounds for named regions"""
        region_bounds = {
            "arabian sea": {"north": 25, "south": 10, "east": 80, "west": 50},
            "bay of bengal": {"north": 25, "south": 5, "east": 100, "west": 80},
            "indian ocean": {"north": 20, "south": -20, "east": 100, "west": 40},
            "equatorial indian ocean": {"north": 10, "south": -10, "east": 100, "west": 40}
        }
        return region_bounds.get(region.lower())
    
    def _identify_region(self, row: pd.Series) -> str:
        """Identify region for a float based on coordinates"""
        lat_min, lat_max = row["LATITUDE_min"], row["LATITUDE_max"]
        lon_min, lon_max = row["LONGITUDE_min"], row["LONGITUDE_max"]
        
        # Simple region identification
        if 10 <= lat_min <= 25 and 50 <= lon_min <= 80:
            return "Arabian Sea"
        elif 5 <= lat_min <= 25 and 80 <= lon_min <= 100:
            return "Bay of Bengal"
        elif -10 <= lat_min <= 10:
            return "Equatorial Indian Ocean"
        else:
            return "Indian Ocean"
```

### 2.5 Visualization Tool

#### 2.5.1 Visualization Tool (`src/mcp/tools/argo_visualization.py`)
```python
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
from src.mcp.tools.base import MCPTool
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ArgoVisualizationTool(MCPTool):
    """Tool for generating ARGO data visualizations"""
    
    def get_name(self) -> str:
        return "generate_plot"
    
    def get_description(self) -> str:
        return "Generate visualization specifications for ARGO data including maps, profiles, and comparisons"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plot_type": {
                    "type": "string",
                    "enum": ["map", "profile", "comparison", "time_series"],
                    "description": "Type of plot to generate"
                },
                "data_query": {
                    "type": "string",
                    "description": "SQL query to get data for visualization"
                },
                "styling": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "colors": {"type": "array", "items": {"type": "string"}},
                        "size": {"type": "object", "properties": {"width": {"type": "number"}, "height": {"type": "number"}}}
                    },
                    "description": "Plot styling options"
                },
                "parameters": {
                    "type": "object",
                    "description": "Plot-specific parameters"
                }
            },
            "required": ["plot_type", "data_query"]
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate plot specification"""
        self.validate_parameters(parameters)
        
        plot_type = parameters["plot_type"]
        data_query = parameters["data_query"]
        styling = parameters.get("styling", {})
        plot_params = parameters.get("parameters", {})
        
        try:
            # Execute data query (simplified - would use ArgoQueryTool)
            data = await self._get_plot_data(data_query)
            
            # Generate plot specification based on type
            if plot_type == "map":
                plot_spec = self._generate_map_plot(data, styling, plot_params)
            elif plot_type == "profile":
                plot_spec = self._generate_profile_plot(data, styling, plot_params)
            elif plot_type == "comparison":
                plot_spec = self._generate_comparison_plot(data, styling, plot_params)
            elif plot_type == "time_series":
                plot_spec = self._generate_time_series_plot(data, styling, plot_params)
            else:
                raise ValueError(f"Unknown plot type: {plot_type}")
            
            return {
                "success": True,
                "plot_specification": plot_spec,
                "plot_type": plot_type,
                "data_points": len(data)
            }
        except Exception as e:
            logger.error(f"Visualization generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_plot_data(self, query: str) -> List[Dict[str, Any]]:
        """Get data for plotting (simplified implementation)"""
        # In real implementation, this would use ArgoQueryTool
        # For now, return mock data
        return [
            {"platform_number": "2901506", "latitude": -6.283, "longitude": 93.509, "temperature": 28.3},
            {"platform_number": "2901507", "latitude": 2.454, "longitude": 46.838, "temperature": 26.1}
        ]
    
    def _generate_map_plot(self, data: List[Dict[str, Any]], styling: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate map plot specification"""
        return {
            "type": "scatter_mapbox",
            "data": {
                "lat": [point["latitude"] for point in data],
                "lon": [point["longitude"] for point in data],
                "text": [point["platform_number"] for point in data],
                "mode": "markers",
                "marker": {
                    "size": 10,
                    "color": "red"
                }
            },
            "layout": {
                "title": styling.get("title", "ARGO Float Locations"),
                "mapbox": {
                    "style": "open-street-map",
                    "center": {"lat": 0, "lon": 70},
                    "zoom": 2
                }
            }
        }
    
    def _generate_profile_plot(self, data: List[Dict[str, Any]], styling: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate profile plot specification"""
        return {
            "type": "scatter",
            "data": {
                "x": [point["temperature"] for point in data],
                "y": [point["latitude"] for point in data],
                "mode": "markers",
                "marker": {
                    "size": 8,
                    "color": "blue"
                }
            },
            "layout": {
                "title": styling.get("title", "Temperature Profile"),
                "xaxis": {"title": "Temperature (°C)"},
                "yaxis": {"title": "Latitude"}
            }
        }
    
    def _generate_comparison_plot(self, data: List[Dict[str, Any]], styling: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison plot specification"""
        return {
            "type": "scatter",
            "data": [
                {
                    "x": [point["temperature"] for point in data],
                    "y": [point["latitude"] for point in data],
                    "mode": "markers",
                    "name": "Temperature vs Latitude"
                }
            ],
            "layout": {
                "title": styling.get("title", "ARGO Data Comparison"),
                "xaxis": {"title": "Temperature (°C)"},
                "yaxis": {"title": "Latitude"}
            }
        }
    
    def _generate_time_series_plot(self, data: List[Dict[str, Any]], styling: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate time series plot specification"""
        return {
            "type": "scatter",
            "data": {
                "x": [point.get("time", "2023-03-01") for point in data],
                "y": [point["temperature"] for point in data],
                "mode": "lines+markers",
                "marker": {"size": 6}
            },
            "layout": {
                "title": styling.get("title", "Temperature Time Series"),
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Temperature (°C)"}
            }
        }
```

### 2.6 MCP Client Implementation

#### 2.6.1 MCP Client (`src/mcp/client.py`)
```python
import asyncio
import json
import websockets
from typing import Dict, Any, List, Optional
from src.mcp.server import MCPMessage, MCPMessageType
from src.utils.logging import get_logger

logger = get_logger(__name__)

class MCPFloatChatClient:
    """MCP client for FloatChat frontend"""
    
    def __init__(self, server_url: str = "ws://localhost:8080"):
        self.server_url = server_url
        self.websocket = None
        self.session_id = None
        self.tools = {}
        self.message_id_counter = 0
    
    async def connect(self) -> bool:
        """Connect to MCP server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Initialize session
            init_message = MCPMessage(
                type=MCPMessageType.INITIALIZE,
                id=self._get_next_message_id(),
                data={"client_info": "FloatChat Frontend"},
                timestamp=asyncio.get_event_loop().time()
            )
            
            response = await self._send_message(init_message)
            if response.type == MCPMessageType.INITIALIZE:
                self.session_id = response.data["session_id"]
                logger.info(f"Connected to MCP server with session: {self.session_id}")
                return True
            else:
                logger.error("Failed to initialize MCP session")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from MCP server"""
        try:
            tools_message = MCPMessage(
                type=MCPMessageType.TOOLS_LIST,
                id=self._get_next_message_id(),
                data={},
                timestamp=asyncio.get_event_loop().time()
            )
            
            response = await self._send_message(tools_message)
            if response.type == MCPMessageType.TOOLS_LIST:
                self.tools = {tool["name"]: tool for tool in response.data["tools"]}
                logger.info(f"Discovered {len(self.tools)} tools")
                return response.data["tools"]
            else:
                logger.error("Failed to discover tools")
                return []
        except Exception as e:
            logger.error(f"Tool discovery error: {e}")
            return []
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on MCP server"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available")
        
        try:
            tool_message = MCPMessage(
                type=MCPMessageType.TOOLS_CALL,
                id=self._get_next_message_id(),
                data={
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "session_id": self.session_id
                },
                timestamp=asyncio.get_event_loop().time()
            )
            
            response = await self._send_message(tool_message)
            if response.type == MCPMessageType.TOOLS_CALL:
                return response.data["result"]
            elif response.type == MCPMessageType.ERROR:
                raise Exception(f"Tool execution error: {response.data['error']}")
            else:
                raise Exception("Unexpected response type")
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            raise
    
    async def process_natural_language(self, query: str) -> str:
        """Process natural language query using MCP tools"""
        try:
            # This would integrate with LLM to determine tool sequence
            # For now, simplified implementation
            
            if "show me" in query.lower() and "map" in query.lower():
                # Use geographic search and visualization tools
                geo_result = await self.call_tool("search_by_location", {"region": "indian ocean"})
                viz_result = await self.call_tool("generate_plot", {
                    "plot_type": "map",
                    "data_query": "SELECT * FROM argo_floats LIMIT 10"
                })
                return f"Found {geo_result['count']} floats. Generated map visualization."
            
            elif "metadata" in query.lower():
                # Use metadata tool
                result = await self.call_tool("get_float_metadata", {"include_statistics": True})
                return f"Retrieved metadata for {result['count']} floats."
            
            else:
                # Use query tool
                result = await self.call_tool("query_argo_database", {
                    "sql_query": "SELECT COUNT(*) as total_floats FROM argo_floats"
                })
                return f"Query executed successfully. Found {result['data'][0]['total_floats']} floats."
        
        except Exception as e:
            logger.error(f"Natural language processing error: {e}")
            return f"Error processing query: {str(e)}"
    
    async def _send_message(self, message: MCPMessage) -> MCPMessage:
        """Send message to MCP server and wait for response"""
        if not self.websocket:
            raise Exception("Not connected to MCP server")
        
        # Send message
        await self.websocket.send(json.dumps({
            "type": message.type.value,
            "id": message.id,
            "data": message.data,
            "timestamp": message.timestamp
        }))
        
        # Wait for response
        response_data = await self.websocket.recv()
        response_json = json.loads(response_data)
        
        return MCPMessage(
            type=MCPMessageType(response_json["type"]),
            id=response_json["id"],
            data=response_json["data"],
            timestamp=response_json["timestamp"]
        )
    
    def _get_next_message_id(self) -> str:
        """Get next message ID"""
        self.message_id_counter += 1
        return f"msg_{self.message_id_counter}"
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
```

## 3. Database Schema for MCP

### 3.1 Enhanced PostgreSQL Schema
```sql
-- ARGO Floats Table
CREATE TABLE argo_floats (
    platform_number VARCHAR(20) PRIMARY KEY,
    latitude_min DECIMAL(10, 6) NOT NULL,
    latitude_max DECIMAL(10, 6) NOT NULL,
    longitude_min DECIMAL(10, 6) NOT NULL,
    longitude_max DECIMAL(10, 6) NOT NULL,
    time_min TIMESTAMP NOT NULL,
    time_max TIMESTAMP NOT NULL,
    region VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ARGO Profiles Table
CREATE TABLE argo_profiles (
    id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES argo_floats(platform_number),
    cycle_number INTEGER NOT NULL,
    pressure DECIMAL(10, 2) NOT NULL,
    temperature DECIMAL(10, 4),
    salinity DECIMAL(10, 4),
    time TIMESTAMP NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    data_mode VARCHAR(10),
    quality_control JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool Execution Log
CREATE TABLE tool_executions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    result JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Context Sessions
CREATE TABLE context_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_profiles_platform ON argo_profiles(platform_number);
CREATE INDEX idx_profiles_time ON argo_profiles(time);
CREATE INDEX idx_profiles_location ON argo_profiles(latitude, longitude);
CREATE INDEX idx_tool_executions_session ON tool_executions(session_id);
CREATE INDEX idx_tool_executions_tool ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_time ON tool_executions(created_at);
```

## 4. Configuration for MCP

### 4.1 MCP Server Configuration
```yaml
# config/mcp_config.yaml
mcp_server:
  host: localhost
  port: 8080
  max_connections: 100
  timeout: 30

database:
  postgresql:
    host: localhost
    port: 5432
    dbname: floatchat_mcp
    user: postgres
    password: 3303
    pool_size: 10

tools:
  argo_query:
    max_query_time: 30
    max_results: 10000
    allowed_tables: ["argo_floats", "argo_profiles"]
  
  argo_metadata:
    cache_ttl: 3600
    max_floats: 1000
  
  argo_geographic:
    max_radius_km: 1000
    default_region: "indian ocean"
  
  argo_visualization:
    max_data_points: 5000
    default_plot_size: {"width": 800, "height": 600}

security:
  sql_validation: true
  rate_limiting: true
  max_requests_per_minute: 60
  allowed_ip_ranges: ["127.0.0.1", "localhost"]
```

## 5. Testing Strategy for MCP

### 5.1 Unit Tests
```python
# tests/test_mcp_tools.py
import pytest
from src.mcp.tools.argo_query import ArgoQueryTool
from src.mcp.tools.argo_metadata import ArgoMetadataTool

class TestArgoQueryTool:
    def test_sql_validation(self):
        """Test SQL query validation"""
        tool = ArgoQueryTool()
        
        # Valid query
        assert tool._validate_sql_query("SELECT * FROM argo_floats LIMIT 10")
        
        # Invalid query
        assert not tool._validate_sql_query("DROP TABLE argo_floats")
    
    def test_tool_specification(self):
        """Test tool specification"""
        tool = ArgoQueryTool()
        spec = tool.get_specification()
        
        assert spec["name"] == "query_argo_database"
        assert "inputSchema" in spec
        assert "sql_query" in spec["inputSchema"]["required"]

class TestArgoMetadataTool:
    def test_metadata_retrieval(self):
        """Test metadata retrieval"""
        tool = ArgoMetadataTool()
        
        # Mock test data
        parameters = {"include_statistics": True}
        context = {}
        
        # This would need proper mocking
        # result = await tool.execute(parameters, context)
        # assert result["success"] == True
```

### 5.2 Integration Tests
```python
# tests/test_mcp_integration.py
import pytest
from src.mcp.client import MCPFloatChatClient

class TestMCPIntegration:
    @pytest.mark.asyncio
    async def test_client_server_communication(self):
        """Test MCP client-server communication"""
        client = MCPFloatChatClient()
        
        # Connect to server
        connected = await client.connect()
        assert connected
        
        # Discover tools
        tools = await client.discover_tools()
        assert len(tools) > 0
        
        # Call tool
        result = await client.call_tool("get_float_metadata", {})
        assert "success" in result
        
        # Disconnect
        await client.disconnect()
```

---

**Document Status**: Draft v1.0  
**Next Review**: October 2024  
**Approval**: Pending technical review
