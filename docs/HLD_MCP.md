# FloatChat - High-Level Design (HLD) Document - MCP Approach

## Document Information
- **Project**: FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data Discovery
- **Version**: 1.0
- **Date**: September 2024
- **Approach**: Model Context Protocol (MCP)
- **Organization**: Ministry of Earth Sciences (MoES) - INCOIS

## 1. Executive Summary

FloatChat MCP implementation leverages the Model Context Protocol to provide structured, tool-based interactions between AI models and oceanographic data systems. This approach offers enhanced reliability, better error handling, and standardized integration patterns for complex oceanographic data queries.

## 2. System Overview

### 2.1 Architecture Pattern
- **Pattern**: MCP Server Architecture with Tool-Based Integration
- **Style**: Protocol-driven, tool-first design
- **Deployment**: MCP Server with client applications

### 2.2 Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   MCP Server    │    │   Database      │
│   (Frontend)    │◄──►│   (Tool Hub)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Tool Registry │
                       │   (ARGO Tools)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Sources  │
                       │   (Argopy, APIs)│
                       └─────────────────┘
```

## 3. MCP Architecture Benefits

### 3.1 Advantages over RAG
- **Structured Tool Access**: Standardized tool interfaces
- **Better Error Handling**: Tool-specific error responses
- **Enhanced Reliability**: Protocol-level guarantees
- **Tool Composition**: Complex operations from simple tools
- **Standardized Integration**: Consistent across different LLM providers

### 3.2 MCP Server Capabilities
- **Tool Discovery**: Automatic tool registration and discovery
- **Context Management**: Persistent context across interactions
- **Resource Management**: Efficient resource utilization
- **Security**: Tool-level access control
- **Monitoring**: Built-in observability

## 4. Functional Requirements

### 4.1 Core MCP Tools
- **ARGO Data Query Tool**: Execute SQL queries on ARGO database
- **Metadata Retrieval Tool**: Get float metadata and statistics
- **Geographic Search Tool**: Find floats by location criteria
- **Temporal Search Tool**: Filter data by time ranges
- **Visualization Tool**: Generate plot specifications
- **Data Export Tool**: Export data in various formats

### 4.2 Tool Specifications
```json
{
  "tools": [
    {
      "name": "query_argo_database",
      "description": "Execute SQL queries on ARGO float database",
      "inputSchema": {
        "type": "object",
        "properties": {
          "sql_query": {
            "type": "string",
            "description": "SQL query to execute"
          },
          "parameters": {
            "type": "object",
            "description": "Query parameters"
          }
        },
        "required": ["sql_query"]
      }
    },
    {
      "name": "get_float_metadata",
      "description": "Retrieve metadata for specific ARGO floats",
      "inputSchema": {
        "type": "object",
        "properties": {
          "platform_numbers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of platform numbers"
          },
          "date_range": {
            "type": "object",
            "properties": {
              "start": {"type": "string"},
              "end": {"type": "string"}
            }
          }
        }
      }
    }
  ]
}
```

## 5. System Architecture

### 5.1 MCP Server Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Server Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Tool Registry  │  Context Manager  │  Resource Manager        │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Implementation Layer                 │
├─────────────────────────────────────────────────────────────────┤
│  ARGO Tools    │  Visualization Tools │  Export Tools          │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Data Access Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Database      │  File System  │  External APIs                │
│  (PostgreSQL)  │  (Parquet)    │  (Argopy, Weather)            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 MCP Client Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application Layer                 │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit UI  │  API Gateway  │  WebSocket Handler            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Tool Client   │  Context Client │  Session Manager            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Integration Layer                    │
├─────────────────────────────────────────────────────────────────┤
│  OpenAI Client │  Anthropic Client │  OpenRouter Client        │
└─────────────────────────────────────────────────────────────────┘
```

## 6. MCP Tool Specifications

### 6.1 ARGO Database Tools

#### 6.1.1 Query Tool
```python
class ArgoQueryTool:
    """Tool for executing SQL queries on ARGO database"""
    
    name = "query_argo_database"
    description = "Execute SQL queries on ARGO float database"
    
    def execute(self, sql_query: str, parameters: dict = None) -> dict:
        """Execute SQL query and return results"""
        - Validate SQL query
        - Execute query with parameters
        - Format results
        - Return structured response
    
    def validate_query(self, sql_query: str) -> bool:
        """Validate SQL query for security"""
        - Check for dangerous operations
        - Validate table names
        - Ensure proper formatting
```

#### 6.1.2 Metadata Tool
```python
class ArgoMetadataTool:
    """Tool for retrieving ARGO float metadata"""
    
    name = "get_float_metadata"
    description = "Get metadata for ARGO floats"
    
    def execute(self, platform_numbers: List[str] = None, 
                date_range: dict = None) -> dict:
        """Retrieve float metadata"""
        - Query float metadata table
        - Filter by platform numbers
        - Filter by date range
        - Return metadata summary
```

#### 6.1.3 Geographic Search Tool
```python
class ArgoGeographicTool:
    """Tool for geographic-based searches"""
    
    name = "search_by_location"
    description = "Find ARGO floats by geographic criteria"
    
    def execute(self, region: str = None, 
                bounds: dict = None,
                depth_range: tuple = None) -> dict:
        """Search floats by geographic criteria"""
        - Parse region names (e.g., "Arabian Sea")
        - Convert to lat/lon bounds
        - Query database
        - Return matching floats
```

### 6.2 Visualization Tools

#### 6.2.1 Plot Generation Tool
```python
class ArgoVisualizationTool:
    """Tool for generating visualization specifications"""
    
    name = "generate_plot"
    description = "Generate plot specifications for ARGO data"
    
    def execute(self, plot_type: str, 
                data_query: str,
                styling: dict = None) -> dict:
        """Generate plot specification"""
        - Validate plot type
        - Execute data query
        - Generate plot configuration
        - Return plot specification
```

### 6.3 Data Export Tools

#### 6.3.1 Export Tool
```python
class ArgoExportTool:
    """Tool for exporting ARGO data"""
    
    name = "export_data"
    description = "Export ARGO data in various formats"
    
    def execute(self, data_query: str,
                format: str = "csv",
                filename: str = None) -> dict:
        """Export data in specified format"""
        - Execute data query
        - Convert to requested format
        - Generate download link
        - Return export information
```

## 7. MCP Server Implementation

### 7.1 Server Configuration
```python
class MCPFloatChatServer:
    """Main MCP server for FloatChat"""
    
    def __init__(self):
        self.tools = self.register_tools()
        self.context_manager = ContextManager()
        self.resource_manager = ResourceManager()
    
    def register_tools(self) -> List[Tool]:
        """Register all available tools"""
        return [
            ArgoQueryTool(),
            ArgoMetadataTool(),
            ArgoGeographicTool(),
            ArgoVisualizationTool(),
            ArgoExportTool()
        ]
    
    def handle_tool_call(self, tool_name: str, parameters: dict) -> dict:
        """Handle tool execution requests"""
        - Find tool by name
        - Validate parameters
        - Execute tool
        - Return results
```

### 7.2 Context Management
```python
class ContextManager:
    """Manage conversation context across tool calls"""
    
    def __init__(self):
        self.sessions = {}
        self.context_history = {}
    
    def create_session(self, session_id: str) -> Session:
        """Create new conversation session"""
        - Initialize session
        - Set up context tracking
        - Return session object
    
    def update_context(self, session_id: str, context: dict):
        """Update session context"""
        - Store context data
        - Maintain history
        - Update session state
    
    def get_context(self, session_id: str) -> dict:
        """Retrieve session context"""
        - Return current context
        - Include relevant history
```

## 8. Client Integration

### 8.1 MCP Client Implementation
```python
class MCPFloatChatClient:
    """MCP client for FloatChat frontend"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools = self.discover_tools()
        self.session_id = self.create_session()
    
    def discover_tools(self) -> List[Tool]:
        """Discover available tools from MCP server"""
        - Connect to MCP server
        - Request tool list
        - Return available tools
    
    def call_tool(self, tool_name: str, parameters: dict) -> dict:
        """Call tool on MCP server"""
        - Validate tool exists
        - Send tool call request
        - Handle response
        - Return results
    
    def process_natural_language(self, query: str) -> dict:
        """Process natural language query using MCP tools"""
        - Parse query intent
        - Determine required tools
        - Execute tool sequence
        - Compose response
```

### 8.2 LLM Integration
```python
class MCPLLMIntegration:
    """Integration between LLM and MCP tools"""
    
    def __init__(self, llm_client, mcp_client):
        self.llm_client = llm_client
        self.mcp_client = mcp_client
    
    def process_query(self, query: str) -> str:
        """Process query using LLM and MCP tools"""
        - Analyze query with LLM
        - Determine tool requirements
        - Execute tools via MCP
        - Generate response with LLM
        - Return final answer
```

## 9. Database Schema for MCP

### 9.1 Enhanced Schema
```sql
-- ARGO Floats Table
CREATE TABLE argo_floats (
    platform_number VARCHAR(20) PRIMARY KEY,
    latitude_min DECIMAL(10, 6),
    latitude_max DECIMAL(10, 6),
    longitude_min DECIMAL(10, 6),
    longitude_max DECIMAL(10, 6),
    time_min TIMESTAMP,
    time_max TIMESTAMP,
    region VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ARGO Profiles Table
CREATE TABLE argo_profiles (
    id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES argo_floats(platform_number),
    cycle_number INTEGER,
    pressure DECIMAL(10, 2),
    temperature DECIMAL(10, 4),
    salinity DECIMAL(10, 4),
    time TIMESTAMP,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    data_mode VARCHAR(10),
    quality_control JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool Execution Log
CREATE TABLE tool_executions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    tool_name VARCHAR(100),
    parameters JSONB,
    result JSONB,
    execution_time_ms INTEGER,
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
```

## 10. Security and Access Control

### 10.1 Tool-Level Security
```python
class ToolSecurityManager:
    """Manage security for MCP tools"""
    
    def __init__(self):
        self.permissions = self.load_permissions()
        self.rate_limits = self.load_rate_limits()
    
    def check_permission(self, user_id: str, tool_name: str) -> bool:
        """Check if user has permission to use tool"""
        - Check user permissions
        - Validate tool access
        - Return permission status
    
    def check_rate_limit(self, user_id: str, tool_name: str) -> bool:
        """Check rate limits for tool usage"""
        - Check usage frequency
        - Validate rate limits
        - Return limit status
```

### 10.2 SQL Injection Prevention
```python
class SQLSecurityValidator:
    """Validate SQL queries for security"""
    
    ALLOWED_TABLES = ['argo_floats', 'argo_profiles']
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']
    
    def validate_query(self, sql_query: str) -> bool:
        """Validate SQL query for security"""
        - Check for dangerous keywords
        - Validate table names
        - Ensure proper formatting
        - Return validation result
```

## 11. Performance and Scalability

### 11.1 Tool Execution Optimization
```python
class ToolExecutionOptimizer:
    """Optimize tool execution performance"""
    
    def __init__(self):
        self.cache = self.setup_cache()
        self.connection_pool = self.setup_connection_pool()
    
    def optimize_query(self, sql_query: str) -> str:
        """Optimize SQL query for performance"""
        - Analyze query plan
        - Suggest optimizations
        - Return optimized query
    
    def cache_results(self, tool_name: str, parameters: dict, results: dict):
        """Cache tool execution results"""
        - Generate cache key
        - Store results
        - Set expiration
```

### 11.2 Resource Management
```python
class MCPResourceManager:
    """Manage MCP server resources"""
    
    def __init__(self):
        self.connection_pool = ConnectionPool()
        self.memory_manager = MemoryManager()
        self.cpu_manager = CPUManager()
    
    def allocate_resources(self, tool_name: str) -> ResourceAllocation:
        """Allocate resources for tool execution"""
        - Check available resources
        - Allocate memory and CPU
        - Return allocation
    
    def release_resources(self, allocation: ResourceAllocation):
        """Release allocated resources"""
        - Free memory
        - Release CPU
        - Update resource status
```

## 12. Monitoring and Observability

### 12.1 Tool Execution Monitoring
```python
class ToolExecutionMonitor:
    """Monitor tool execution performance"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerting = AlertingSystem()
    
    def track_execution(self, tool_name: str, duration: float, success: bool):
        """Track tool execution metrics"""
        - Record execution time
        - Track success rate
        - Update performance metrics
        - Trigger alerts if needed
    
    def generate_report(self) -> dict:
        """Generate performance report"""
        - Aggregate metrics
        - Calculate statistics
        - Return report
```

### 12.2 Context Tracking
```python
class ContextTracker:
    """Track conversation context and tool usage"""
    
    def __init__(self):
        self.context_store = ContextStore()
        self.usage_analytics = UsageAnalytics()
    
    def track_context_change(self, session_id: str, context: dict):
        """Track context changes"""
        - Store context snapshot
        - Analyze context evolution
        - Update usage patterns
    
    def analyze_usage_patterns(self) -> dict:
        """Analyze tool usage patterns"""
        - Aggregate usage data
        - Identify patterns
        - Return analysis
```

## 13. Deployment Architecture

### 13.1 MCP Server Deployment
```yaml
# docker-compose.yml for MCP Server
version: '3.8'
services:
  mcp-server:
    build: ./mcp-server
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/floatchat
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=floatchat
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
```

### 13.2 Client Deployment
```yaml
# docker-compose.yml for Client
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - MCP_SERVER_URL=http://mcp-server:8080
  
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    environment:
      - MCP_SERVER_URL=http://mcp-server:8080
```

## 14. Migration Strategy

### 14.1 From RAG to MCP
```python
class RAGToMCPMigrator:
    """Migrate from RAG to MCP implementation"""
    
    def migrate_data(self):
        """Migrate data from RAG to MCP format"""
        - Convert ChromaDB to PostgreSQL
        - Migrate metadata
        - Update data structures
    
    def migrate_queries(self):
        """Migrate query processing"""
        - Convert RAG queries to MCP tools
        - Update query logic
        - Test compatibility
    
    def migrate_frontend(self):
        """Migrate frontend to MCP client"""
        - Update API calls
        - Implement MCP client
        - Test functionality
```

## 15. Future Enhancements

### 15.1 Advanced MCP Features
- **Tool Composition**: Complex operations from simple tools
- **Dynamic Tool Loading**: Runtime tool registration
- **Cross-Server Communication**: Multi-server MCP networks
- **Tool Versioning**: Versioned tool interfaces
- **Advanced Context**: Multi-modal context management

### 15.2 Integration Enhancements
- **Real-time Data**: Live ARGO data streaming
- **Satellite Integration**: Combined in-situ and remote sensing
- **Predictive Tools**: Oceanographic forecasting tools
- **Collaborative Tools**: Multi-user tool sessions

---

**Document Status**: Draft v1.0  
**Next Review**: October 2024  
**Approval**: Pending technical review
