# FloatChat - Detailed Project Working Documentation

## Document Information
- **Project**: FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data Discovery
- **Version**: 1.0
- **Date**: September 2024
- **Organization**: Ministry of Earth Sciences (MoES) - INCOIS

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [RAG Implementation - Detailed Working](#2-rag-implementation---detailed-working)
3. [MCP Implementation - Detailed Working](#3-mcp-implementation---detailed-working)
4. [System Architecture Comparison](#4-system-architecture-comparison)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Component Interactions](#6-component-interactions)
7. [Deployment and Operations](#7-deployment-and-operations)

---

## 1. Project Overview

FloatChat is an AI-powered conversational system that enables users to query ARGO float oceanographic data using natural language. The system supports two implementation approaches:

- **RAG (Retrieval-Augmented Generation)**: Current implementation using vector search and LLM integration
- **MCP (Model Context Protocol)**: Future implementation using structured tool-based interactions

### 1.1 Core Problem Statement
Oceanographers and researchers need to:
- Query complex ARGO float data using natural language
- Visualize oceanographic parameters interactively
- Export data for further analysis
- Compare data across different regions and time periods

### 1.2 Solution Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    FloatChat System                            │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)  │  API Layer  │  AI Processing Layer    │
│  - Chat Interface      │  - FastAPI   │  - RAG Pipeline         │
│  - Dashboard          │  - Routes    │  - MCP Tools           │
│  - Visualizations     │  - Schemas   │  - LLM Integration     │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                   │
├─────────────────────────────────────────────────────────────────┤
│  Vector DB (ChromaDB)  │  Relational DB  │  File Storage      │
│  - Metadata Embeddings  │  - PostgreSQL   │  - Parquet/NetCDF   │
│  - Similarity Search    │  - Structured   │  - Processed Data   │
│  - Context Retrieval    │  - Queries      │  - Raw Data        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. RAG Implementation - Detailed Working

### 2.1 RAG Architecture Overview

The RAG (Retrieval-Augmented Generation) implementation uses a vector database to store ARGO metadata and retrieves relevant information to augment LLM responses.

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Pipeline Flow                           │
├─────────────────────────────────────────────────────────────────┤
│  User Query → Vector Search → Context Retrieval → LLM → Response│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Detailed Component Breakdown

#### 2.2.1 Data Ingestion Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Process                      │
├─────────────────────────────────────────────────────────────────┤
│  ARGO NetCDF Files → Argopy → Data Processing → Vector Embeddings│
└─────────────────────────────────────────────────────────────────┘
```

**Step-by-Step Process:**

1. **Raw Data Acquisition**
   ```python
   # src/data_ingestion/ingest_argo.py
   def ingest_argo_data():
       # Fetch ARGO data using argopy
       ds = argopy.DataFetcher().region([
           40, 100,    # Longitude: 40°E to 100°E
           -20, 20,    # Latitude: 20°S to 20°N
           0, 1000,    # Depth: 0m to 1000m
           '2023-03', '2023-04'  # Time: March-April 2023
       ]).to_xarray()
       
       # Convert to DataFrame
       df = ds.to_dataframe()
       df.to_parquet("data/processed/argo_data.parquet")
   ```

2. **Metadata Extraction**
   ```python
   # src/data_ingestion/metadata_extractor.py
   def extract_metadata():
       df = pd.read_parquet("data/processed/argo_data.parquet")
       
       # Group by platform number and calculate ranges
       metadata = df.groupby('PLATFORM_NUMBER').agg({
           'LATITUDE': ['min', 'max'],
           'LONGITUDE': ['min', 'max'],
           'TIME': ['min', 'max']
       }).reset_index()
       
       # Flatten column names
       metadata.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] 
                          for col in metadata.columns]
       
       metadata.to_csv("data/processed/metadata.csv")
   ```

3. **Vector Database Population**
   ```python
   # src/database/vector_db.py
   def init_vector_db(metadata):
       # Create ChromaDB collection with embeddings
       client = chromadb.PersistentClient(path="./chroma_db")
       collection = client.create_collection(
           "argo_metadata",
           embedding_function=embedding_functions.DefaultEmbeddingFunction()
       )
       
       # Add metadata as documents
       for idx, row in metadata.iterrows():
           doc = f"Float {row['PLATFORM_NUMBER']}: " \
                 f"Lat {row['LATITUDE_min']}-{row['LATITUDE_max']}, " \
                 f"Lon {row['LONGITUDE_min']}-{row['LONGITUDE_max']}, " \
                 f"Time {row['TIME_min']}-{row['TIME_max']}"
           
           collection.add(
               documents=[doc],
               ids=[str(row['PLATFORM_NUMBER'])]
           )
   ```

#### 2.2.2 RAG Pipeline Implementation

**Custom ChromaDB Retriever:**
```python
# src/llm/rag_pipeline.py
class ChromaRetriever(BaseRetriever):
    """Custom retriever for ChromaDB integration"""
    
    collection: object = Field(exclude=True)
    
    def get_relevant_documents(self, query: str):
        """Retrieve relevant documents from ChromaDB"""
        results = self.collection.query(
            query_texts=[query],
            n_results=3
        )
        
        documents = []
        if results['documents'] and results['documents'][0]:
            for doc in results['documents'][0]:
                documents.append(Document(page_content=doc))
        
        return documents
```

**RAG Chain Setup:**
```python
def setup_rag(metadata, llm_type="mock"):
    # Step 1: Initialize ChromaDB collection
    collection = init_vector_db(metadata)
    
    # Step 2: Create custom retriever
    retriever = ChromaRetriever(collection=collection)
    
    # Step 3: Get LLM instance
    llm = get_llm(model_type=llm_type)
    
    # Step 4: Define prompt template
    prompt_template = """
    You are FloatChat, an AI-powered ocean data assistant specializing in ARGO float data analysis.
    
    ARGO Float Context:
    {context}
    
    User Question: {question}
    
    Instructions:
    - Provide specific float IDs, coordinates, and time ranges
    - Suggest using the dashboard for detailed visualizations
    - Generate SQL queries for data retrieval
    
    **SQL Query:**
    ```sql
    [Your generated SQL query here]
    ```
    
    **Answer:**
    [Your detailed response here]
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question", "context"]
    )
    
    # Step 5: Build RetrievalQA chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return chain
```

#### 2.2.3 LLM Integration

**Multi-Provider LLM Support:**
```python
# src/llm/models.py
def get_llm(model_type="mock", **kwargs):
    """Factory function to get LLM instance"""
    config = load_config()
    
    if model_type == "openai":
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            api_key=config.get("llm", {}).get("api_key")
        )
    elif model_type == "openrouter":
        return ChatOpenAI(
            model="deepseek/deepseek-chat-v3.1:free",
            api_key=config.get("llm", {}).get("api_key"),
            base_url="https://openrouter.ai/api/v1"
        )
    elif model_type == "anthropic":
        return ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.1,
            api_key=config.get("llm", {}).get("api_key")
        )
    else:
        return MockLLM()
```

### 2.3 RAG Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Query Processing                        │
├─────────────────────────────────────────────────────────────────┤
│  1. User Input → 2. Vector Search → 3. Context Retrieval        │
│  4. LLM Processing → 5. SQL Generation → 6. Response Formatting │
└─────────────────────────────────────────────────────────────────┘
```

**Detailed Flow:**

1. **User Query Reception**
   ```python
   # src/api/routes/chat.py
   @router.post("/chat", response_model=QueryResponse)
   async def chat_query(query: QueryInput):
       # Determine LLM type from config
       config = load_config()
       llm_type = determine_llm_type(config)
       
       # Setup RAG pipeline
       metadata = extract_metadata()
       rag_chain = setup_rag(metadata, llm_type=llm_type)
       
       # Execute query
       response = run_rag_query(rag_chain, query.text)
       return QueryResponse(response=response)
   ```

2. **Vector Search Execution**
   ```python
   def run_rag_query(chain, question):
       # Execute RAG chain
       result = chain.invoke({"query": question})
       
       # Extract SQL query from response
       sql_query = extract_sql_query(result["result"])
       
       # Log SQL query
       if sql_query:
           logger.info("=" * 80)
           logger.info("🔍 GENERATED SQL QUERY:")
           logger.info("=" * 80)
           logger.info(sql_query)
           logger.info("=" * 80)
       
       return result["result"]
   ```

3. **SQL Query Extraction**
   ```python
   def extract_sql_query(response_text):
       """Extract SQL query from LLM response"""
       import re
       
       # Look for SQL query in code blocks
       sql_pattern = r'```sql\s*(.*?)\s*```'
       match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
       
       if match:
           return match.group(1).strip()
       
       return None
   ```

### 2.4 Frontend Integration

**Streamlit Chat Interface:**
```python
# src/frontend/chat_interface.py
def main():
    st.title("🌊 FloatChat - ARGO Ocean Data Assistant")
    
    # Example queries
    example_queries = [
        "Show me salinity profiles near the equator in March 2023",
        "Compare BGC parameters in the Arabian Sea for the last 6 months",
        "What are the nearest ARGO floats to this location?"
    ]
    
    # Display examples
    for query in example_queries:
        if st.button(f"💬 {query}"):
            st.session_state.user_input = query
    
    # Chat interface
    if prompt := st.chat_input("Ask about ARGO data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Call API
        response = requests.post(
            "http://localhost:8000/chat", 
            json={"text": prompt}
        ).json()
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response["response"]
        })
```

**Dashboard Visualization:**
```python
# src/frontend/pages/dashboard.py
def plot_argo_trajectories(metadata):
    """Create map visualization of ARGO float locations"""
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=metadata['LATITUDE_min'],
        lon=metadata['LONGITUDE_min'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='red'
        ),
        text=metadata['PLATFORM_NUMBER'],
        hovertemplate='<b>Float %{text}</b><br>' +
                     'Lat: %{lat}<br>' +
                     'Lon: %{lon}<extra></extra>'
    ))
    
    fig.update_layout(
        title="ARGO Float Locations",
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=0, lon=70),
            zoom=2
        )
    )
    
    return fig
```

---

## 3. MCP Implementation - Detailed Working

### 3.1 MCP Architecture Overview

The MCP (Model Context Protocol) implementation uses structured tools to provide reliable, tool-based interactions between AI models and oceanographic data systems.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Architecture Flow                       │
├─────────────────────────────────────────────────────────────────┤
│  User Query → Tool Selection → Tool Execution → Response Assembly│
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 MCP Server Implementation

#### 3.2.1 MCP Protocol Handler
```python
# src/mcp/server.py
class MCPFloatChatServer:
    """Main MCP server implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.tools = self._register_tools()
        self.context_manager = ContextManager()
        self.sessions = {}
    
    def _register_tools(self) -> Dict[str, 'MCPTool']:
        """Register all available MCP tools"""
        return {
            "query_argo_database": ArgoQueryTool(),
            "get_float_metadata": ArgoMetadataTool(),
            "search_by_location": ArgoGeographicTool(),
            "generate_plot": ArgoVisualizationTool(),
            "export_data": ArgoExportTool()
        }
    
    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP messages"""
        if message.type == MCPMessageType.TOOLS_CALL:
            return await self._handle_tool_call(message)
        elif message.type == MCPMessageType.TOOLS_LIST:
            return await self._handle_tools_list(message)
        # ... other message types
```

#### 3.2.2 Tool Base Class
```python
# src/mcp/tools/base.py
class MCPTool(ABC):
    """Base class for MCP tools"""
    
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
```

### 3.3 MCP Tools Implementation

#### 3.3.1 ARGO Database Query Tool
```python
# src/mcp/tools/argo_query.py
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
                    "description": "Query parameters for prepared statements"
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
        sql_query = parameters["sql_query"]
        query_params = parameters.get("parameters", {})
        limit = parameters.get("limit", 1000)
        
        # Security validation
        if not self._validate_sql_query(sql_query):
            raise ValueError("SQL query failed security validation")
        
        # Execute query
        results = await self._execute_query(sql_query, query_params, limit)
        
        return {
            "success": True,
            "data": results,
            "row_count": len(results),
            "query": sql_query
        }
    
    def _validate_sql_query(self, sql_query: str) -> bool:
        """Validate SQL query for security"""
        sql_upper = sql_query.upper()
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        # Check for allowed tables
        allowed_tables = ['argo_floats', 'argo_profiles']
        for table in allowed_tables:
            if table in sql_upper:
                return True
        
        return False
```

#### 3.3.2 Geographic Search Tool
```python
# src/mcp/tools/argo_geographic.py
class ArgoGeographicTool(MCPTool):
    """Tool for geographic-based ARGO float searches"""
    
    def get_name(self) -> str:
        return "search_by_location"
    
    def get_description(self) -> str:
        return "Find ARGO floats by geographic criteria including regions, coordinates, and depth ranges"
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Search ARGO floats by geographic criteria"""
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
        
        return filtered_df
    
    def _get_region_bounds(self, region: str) -> Dict[str, float]:
        """Get geographic bounds for named regions"""
        region_bounds = {
            "arabian sea": {"north": 25, "south": 10, "east": 80, "west": 50},
            "bay of bengal": {"north": 25, "south": 5, "east": 100, "west": 80},
            "indian ocean": {"north": 20, "south": -20, "east": 100, "west": 40}
        }
        return region_bounds.get(region.lower())
```

### 3.4 MCP Client Implementation

#### 3.4.1 MCP Client
```python
# src/mcp/client.py
class MCPFloatChatClient:
    """MCP client for FloatChat frontend"""
    
    def __init__(self, server_url: str = "ws://localhost:8080"):
        self.server_url = server_url
        self.websocket = None
        self.session_id = None
        self.tools = {}
    
    async def connect(self) -> bool:
        """Connect to MCP server"""
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
            return True
        return False
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on MCP server"""
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
    
    async def process_natural_language(self, query: str) -> str:
        """Process natural language query using MCP tools"""
        # Determine tool sequence based on query
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
```

### 3.5 MCP Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Query Processing                        │
├─────────────────────────────────────────────────────────────────┤
│  1. User Input → 2. Tool Selection → 3. Tool Execution         │
│  4. Result Processing → 5. Response Assembly → 6. Output       │
└─────────────────────────────────────────────────────────────────┘
```

**Detailed Flow:**

1. **Query Analysis and Tool Selection**
   ```python
   def analyze_query_intent(query: str) -> List[str]:
       """Analyze query to determine required tools"""
       tools_needed = []
       
       if "location" in query.lower() or "region" in query.lower():
           tools_needed.append("search_by_location")
       
       if "metadata" in query.lower() or "information" in query.lower():
           tools_needed.append("get_float_metadata")
       
       if "query" in query.lower() or "select" in query.lower():
           tools_needed.append("query_argo_database")
       
       if "plot" in query.lower() or "visualize" in query.lower():
           tools_needed.append("generate_plot")
       
       return tools_needed
   ```

2. **Tool Execution Sequence**
   ```python
   async def execute_tool_sequence(tools: List[str], query: str, client: MCPFloatChatClient) -> Dict[str, Any]:
       """Execute tools in sequence"""
       results = {}
       
       for tool in tools:
           if tool == "search_by_location":
               # Extract location parameters from query
               location_params = extract_location_params(query)
               results[tool] = await client.call_tool(tool, location_params)
           
           elif tool == "get_float_metadata":
               # Extract metadata parameters
               metadata_params = extract_metadata_params(query)
               results[tool] = await client.call_tool(tool, metadata_params)
           
           # ... other tools
       
       return results
   ```

3. **Response Assembly**
   ```python
   def assemble_response(tool_results: Dict[str, Any], original_query: str) -> str:
       """Assemble final response from tool results"""
       response_parts = []
       
       # Add introduction
       response_parts.append(f"Based on your query: '{original_query}'")
       
       # Process each tool result
       for tool_name, result in tool_results.items():
           if tool_name == "search_by_location":
               response_parts.append(f"Found {result['count']} ARGO floats in the specified region.")
               for float_data in result['data'][:5]:  # Show first 5
                   response_parts.append(f"- Float {float_data['platform_number']}: {float_data['region']}")
           
           elif tool_name == "get_float_metadata":
               response_parts.append(f"Retrieved metadata for {result['count']} floats.")
               if 'statistics' in result:
                   stats = result['statistics']
                   response_parts.append(f"Geographic coverage: {stats['latitude_range']['min']}°N to {stats['latitude_range']['max']}°N")
       
       return "\n".join(response_parts)
   ```

---

## 4. System Architecture Comparison

### 4.1 RAG vs MCP Comparison

| Aspect | RAG Implementation | MCP Implementation |
|--------|-------------------|-------------------|
| **Architecture** | Vector-based retrieval | Tool-based execution |
| **Reliability** | Depends on vector similarity | Structured tool responses |
| **Error Handling** | LLM-dependent | Tool-specific validation |
| **Scalability** | Vector DB limitations | Tool composition |
| **Security** | Prompt injection risks | Tool-level access control |
| **Maintenance** | Vector DB management | Tool versioning |

### 4.2 Performance Characteristics

**RAG Performance:**
- Query Processing: 2-5 seconds
- Vector Search: 100-500ms
- LLM Generation: 1-3 seconds
- Memory Usage: High (embeddings)

**MCP Performance:**
- Query Processing: 1-3 seconds
- Tool Execution: 200-800ms
- Response Assembly: 100-300ms
- Memory Usage: Low (tool instances)

---

## 5. Data Flow Diagrams

### 5.1 RAG Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Data Flow Diagram                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Frontend  │───►│   API       │───►│   RAG       │        │
│  │ (Streamlit) │    │ (FastAPI)   │    │ Pipeline    │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                │               │
│                                ▼                ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Response  │◄───│   LLM       │◄───│   Vector    │        │
│  │   Display   │    │ Processing  │    │ Search      │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                │               │
│                                ▼                ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   SQL       │    │   Context   │    │   ChromaDB  │        │
│  │ Generation  │    │ Retrieval   │    │ Collection  │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 MCP Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Data Flow Diagram                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Frontend  │───►│   MCP       │───►│   Tool      │        │
│  │ (Streamlit) │    │   Client    │    │ Selection   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                │               │
│                                ▼                ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Response  │◄───│   MCP       │◄───│   Tool      │        │
│  │   Assembly  │    │   Server    │    │ Execution   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                │               │
│                                ▼                ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Context   │    │   Tool      │    │   Database  │        │
│  │ Management  │    │ Registry    │    │ (PostgreSQL)│        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                Component Interaction Diagram                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   User      │    │   Frontend  │    │   API       │        │
│  │ Interface   │◄──►│   Layer      │◄──►│   Gateway   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                │               │
│                                ▼                ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   RAG       │    │   MCP       │    │   Data      │        │
│  │ Pipeline    │    │   Server    │    │ Processing  │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                │                │                    │
│         ▼                ▼                ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Vector    │    │   Tool      │    │   File      │        │
│  │ Database    │    │ Registry    │    │ Storage     │        │
│  │ (ChromaDB)  │    │             │    │ (Parquet)   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                │                                │
│                                ▼                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   LLM       │    │   Relational│    │   External  │        │
│  │ Services    │    │   Database  │    │   APIs      │        │
│  │ (OpenRouter)│    │ (PostgreSQL)│    │ (Argopy)    │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Component Interactions

### 6.1 RAG Component Interactions

**Frontend to API:**
```python
# Frontend sends query to API
response = requests.post(
    "http://localhost:8000/chat",
    json={"text": "Show me salinity profiles near the equator"}
)

# API processes query through RAG pipeline
@router.post("/chat")
async def chat_query(query: QueryInput):
    metadata = extract_metadata()
    rag_chain = setup_rag(metadata, llm_type="openrouter")
    response = run_rag_query(rag_chain, query.text)
    return QueryResponse(response=response)
```

**RAG Pipeline to Vector DB:**
```python
# RAG pipeline queries ChromaDB
def get_relevant_documents(self, query: str):
    results = self.collection.query(
        query_texts=[query],
        n_results=3
    )
    return [Document(page_content=doc) for doc in results['documents'][0]]
```

**LLM Integration:**
```python
# LLM processes context and generates response
chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)
```

### 6.2 MCP Component Interactions

**Frontend to MCP Client:**
```python
# Frontend uses MCP client
client = MCPFloatChatClient("ws://localhost:8080")
await client.connect()
result = await client.call_tool("search_by_location", {"region": "arabian sea"})
```

**MCP Client to Server:**
```python
# MCP client sends tool call to server
tool_message = MCPMessage(
    type=MCPMessageType.TOOLS_CALL,
    id=self._get_next_message_id(),
    data={
        "tool_name": tool_name,
        "parameters": parameters,
        "session_id": self.session_id
    }
)
```

**Tool Execution:**
```python
# Tool executes with context
async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]):
    # Validate parameters
    self.validate_parameters(parameters)
    
    # Execute tool logic
    result = await self._execute_tool_logic(parameters, context)
    
    return {"success": True, "data": result}
```

---

## 7. Deployment and Operations

### 7.1 RAG Deployment

**Docker Compose for RAG:**
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
  
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/floatchat
      - CHROMADB_PATH=/app/chroma_db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=floatchat
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 7.2 MCP Deployment

**Docker Compose for MCP:**
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - MCP_SERVER_URL=ws://mcp-server:8080
  
  mcp-server:
    build: ./mcp-server
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/floatchat_mcp
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=floatchat_mcp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 7.3 Monitoring and Logging

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

def log_query_execution(query: str, response: str, duration: float):
    logger.info(
        "query_executed",
        query=query,
        response_length=len(response),
        duration_ms=duration * 1000,
        timestamp=datetime.utcnow().isoformat()
    )
```

**Metrics Collection:**
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('floatchat_queries_total', 'Total number of queries')
query_duration = Histogram('floatchat_query_duration_seconds', 'Query duration')

def track_query_metrics(func):
    def wrapper(*args, **kwargs):
        query_counter.inc()
        with query_duration.time():
            return func(*args, **kwargs)
    return wrapper
```

---

## Conclusion

FloatChat provides two complementary approaches for AI-powered oceanographic data querying:

1. **RAG Implementation**: Current solution using vector search and LLM integration for flexible natural language processing
2. **MCP Implementation**: Future solution using structured tools for reliable, tool-based interactions

Both approaches serve the same goal of making ARGO float data accessible through conversational interfaces, but offer different trade-offs in terms of reliability, maintainability, and performance characteristics.

The system is designed to be scalable, secure, and maintainable, with comprehensive monitoring and logging capabilities to support production deployment in oceanographic research environments.

---

