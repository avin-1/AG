# FloatChat - Low-Level Design (LLD) Document

## Document Information
- **Project**: FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data Discovery
- **Version**: 1.0
- **Date**: September 2024
- **Approach**: Retrieval-Augmented Generation (RAG)
- **Organization**: Ministry of Earth Sciences (MoES) - INCOIS

## 1. Overview

This document provides detailed technical specifications for the FloatChat RAG implementation, including class diagrams, API specifications, database schemas, and implementation details.

## 2. System Components Detail

### 2.1 Frontend Components

#### 2.1.1 Chat Interface (`src/frontend/chat_interface.py`)
```python
class ChatInterface:
    """Main Streamlit chat interface"""
    
    def __init__(self):
        self.session_state = st.session_state
        self.api_client = APIClient()
    
    def render_interface(self):
        """Render the main chat interface"""
        - Display title and description
        - Show example queries
        - Render chat messages
        - Handle user input
    
    def send_message(self, message: str) -> str:
        """Send message to API and return response"""
        - Validate input
        - Call API endpoint
        - Handle errors
        - Update session state
    
    def display_examples(self):
        """Display example queries"""
        - Render example buttons
        - Handle example selection
```

#### 2.1.2 Dashboard (`src/frontend/pages/dashboard.py`)
```python
class Dashboard:
    """Interactive data visualization dashboard"""
    
    def load_argo_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load ARGO data from processed files"""
        - Read parquet files
        - Load metadata CSV
        - Handle file errors
    
    def plot_argo_trajectories(self, metadata: pd.DataFrame) -> go.Figure:
        """Create map visualization of ARGO float locations"""
        - Use Plotly scatter_mapbox
        - Configure map styling
        - Add hover information
    
    def plot_depth_time_profile(self, df: pd.DataFrame, float_id: str = None) -> go.Figure:
        """Create depth-time profile visualization"""
        - Filter data by float ID
        - Create scatter plot
        - Configure color mapping
    
    def plot_salinity_comparison(self, df: pd.DataFrame) -> go.Figure:
        """Compare salinity profiles across floats"""
        - Group by platform number
        - Create line plots
        - Add legends and styling
```

### 2.2 API Components

#### 2.2.1 Main API (`src/api/main.py`)
```python
class FloatChatAPI:
    """Main FastAPI application"""
    
    def __init__(self):
        self.app = FastAPI(title="FloatChat API")
        self.setup_routes()
        self.setup_middleware()
    
    def setup_routes(self):
        """Configure API routes"""
        - Include chat router
        - Include data router
        - Add health check
    
    def setup_middleware(self):
        """Configure middleware"""
        - CORS middleware
        - Request logging
        - Error handling
```

#### 2.2.2 Chat Router (`src/api/routes/chat.py`)
```python
class ChatRouter:
    """Handle chat-related API endpoints"""
    
    @router.post("/chat", response_model=QueryResponse)
    async def chat_query(self, query: QueryInput) -> QueryResponse:
        """Process natural language queries"""
        - Load configuration
        - Determine LLM type
        - Setup RAG pipeline
        - Execute query
        - Return response
    
    def load_config(self) -> dict:
        """Load configuration from YAML"""
        - Read config file
        - Handle errors
        - Return config dict
    
    def determine_llm_type(self, config: dict) -> str:
        """Determine which LLM to use based on config"""
        - Check API key format
        - Map model names
        - Return LLM type
```

#### 2.2.3 Data Router (`src/api/routes/data.py`)
```python
class DataRouter:
    """Handle data-related API endpoints"""
    
    @router.get("/data")
    async def get_data(self, query: str) -> dict:
        """Execute SQL queries"""
        - Validate query
        - Execute SQL
        - Return results
    
    @router.get("/metadata")
    async def get_metadata(self) -> dict:
        """Get ARGO metadata summary"""
        - Load metadata
        - Calculate statistics
        - Return summary
```

### 2.3 RAG Pipeline Components

#### 2.3.1 RAG Pipeline (`src/llm/rag_pipeline.py`)
```python
class ChromaRetriever(BaseRetriever):
    """Custom retriever for ChromaDB integration"""
    
    collection: object = Field(exclude=True)
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve relevant documents from ChromaDB"""
        - Query ChromaDB collection
        - Convert results to Documents
        - Handle errors
        - Return document list

def setup_rag(metadata: pd.DataFrame, llm_type: str = "mock") -> RetrievalQA:
    """Setup RAG pipeline with specified LLM"""
    - Initialize ChromaDB collection
    - Create custom retriever
    - Get LLM instance
    - Define prompt template
    - Build RetrievalQA chain
    - Return configured chain

def run_rag_query(chain: RetrievalQA, question: str) -> str:
    """Execute RAG query and return response"""
    - Invoke chain with question
    - Extract SQL query from response
    - Log SQL query to terminal
    - Return response text

def extract_sql_query(response_text: str) -> Optional[str]:
    """Extract SQL query from LLM response"""
    - Use regex patterns
    - Look for code blocks
    - Return extracted query
```

#### 2.3.2 LLM Models (`src/llm/models.py`)
```python
class MockLLM(LLM):
    """Mock LLM for testing and development"""
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate mock response"""
        - Log prompt
        - Return mock response
    
    @property
    def _llm_type(self) -> str:
        """Return LLM type"""
        return "mock"

def get_llm(model_type: str = "mock", **kwargs) -> LLM:
    """Factory function to get LLM instance"""
    - Load configuration
    - Check API keys
    - Return appropriate LLM:
        * ChatOpenAI (OpenAI/OpenRouter)
        * ChatAnthropic (Anthropic)
        * HuggingFaceEndpoint (HuggingFace)
        * MockLLM (fallback)
```

### 2.4 Data Components

#### 2.4.1 Data Ingestion (`src/data_ingestion/ingest_argo.py`)
```python
def ingest_argo_data():
    """Ingest ARGO data using argopy"""
    - Load configuration
    - Setup directories
    - Fetch ARGO data:
        * Region: Indian Ocean (40°E-100°E, 20°S-20°N)
        * Time: March-April 2023
        * Depth: 0-1000m
    - Convert to DataFrame
    - Save as Parquet

def load_config() -> dict:
    """Load configuration from YAML"""
    - Read config file
    - Return configuration dict
```

#### 2.4.2 Metadata Extractor (`src/data_ingestion/metadata_extractor.py`)
```python
def extract_metadata() -> pd.DataFrame:
    """Extract metadata from ARGO data"""
    - Load parquet data
    - Detect column names:
        * PLATFORM_NUMBER
        * LATITUDE
        * LONGITUDE
        * TIME
    - Group by platform number
    - Calculate min/max values
    - Flatten column names
    - Save to CSV
    - Return metadata DataFrame
```

#### 2.4.3 Vector Database (`src/database/vector_db.py`)
```python
def init_vector_db(metadata: pd.DataFrame) -> Collection:
    """Initialize ChromaDB with ARGO metadata"""
    - Create embedding function
    - Create persistent client
    - Get or create collection
    - Add metadata documents:
        * Format: "Float {id}: Lat {min}-{max}, Lon {min}-{max}, Time {min}-{max}"
        * ID: platform number
    - Return collection

def get_collection() -> Collection:
    """Get existing ChromaDB collection"""
    - Create client
    - Return collection
    - Handle missing collection
```

## 3. Database Schema

### 3.1 Vector Database (ChromaDB)
```python
# Collection: argo_metadata
{
    "id": "PLATFORM_NUMBER",  # e.g., "2901506"
    "document": "Float 2901506: Lat -6.283--6.19, Lon 93.509-94.373, Time 2023-03-03 02:31:14-2023-03-24 14:22:25",
    "metadata": {
        "platform_number": "2901506",
        "latitude_min": -6.283,
        "latitude_max": -6.19,
        "longitude_min": 93.509,
        "longitude_max": 94.373,
        "time_min": "2023-03-03 02:31:14",
        "time_max": "2023-03-24 14:22:25"
    }
}
```

### 3.2 Relational Database (PostgreSQL) - Future
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    quality_control JSONB
);

-- Indexes for performance
CREATE INDEX idx_profiles_platform ON argo_profiles(platform_number);
CREATE INDEX idx_profiles_time ON argo_profiles(time);
CREATE INDEX idx_profiles_location ON argo_profiles(latitude, longitude);
```

### 3.3 File Storage Schema
```
data/
├── raw/                    # Raw NetCDF files
│   ├── argo_netcdf/
│   └── metadata/
├── processed/              # Processed data files
│   ├── argo_data.parquet  # Main dataset
│   ├── metadata.csv       # Float metadata
│   └── embeddings/        # Vector embeddings
└── cache/                 # Argopy cache
    └── erddap/
```

## 4. API Specifications

### 4.1 Chat API Endpoints

#### 4.1.1 POST /chat
```python
# Request
{
    "text": "Show me salinity profiles near the equator in March 2023"
}

# Response
{
    "response": "Based on the ARGO float data available, here's what was active during March 2023:\n\n## March 2023 ARGO Float Data Availability\n\n### Active Floats:\n1. **Float 5906536**\n   - **Location**: Southwest Indian Ocean (-19.61°S to -19.24°S, 54.18°E to 54.52°E)\n   - **Time Range**: March 9, 2023 (05:36) to March 29, 2023 (20:26)\n   - **Region**: Mascarene Basin area\n\n2. **Float 1902054**\n   - **Location**: Eastern Indian Ocean near Sumatra (-14.18°S to -13.99°S, 92.25°E to 92.34°E)\n   - **Time Range**: March 3, 2023 (15:35) to March 23, 2023 (10:53)\n   - **Region**: Eastern equatorial Indian Ocean\n\n## Available Parameters:\nAll floats provide standard ARGO measurements:\n- **Temperature (TEMP)** profiles\n- **Salinity (PSAL)** profiles\n- **Pressure (PRES)** data\n\n## Next Steps:\nTo explore this March 2023 data further, I recommend:\n1. Using the dashboard to visualize temperature and salinity profiles from these floats\n2. Comparing conditions between the eastern and western Indian Ocean regions\n3. Examining any seasonal patterns or anomalies during this period"
}
```

#### 4.1.2 GET /data
```python
# Request
GET /data?query=SELECT * FROM argo_profiles WHERE platform_number = '2901506'

# Response
{
    "results": [
        {
            "platform_number": "2901506",
            "cycle_number": 1,
            "pressure": 10.5,
            "temperature": 28.3,
            "salinity": 35.2,
            "time": "2023-03-03T02:31:14Z",
            "latitude": -6.283,
            "longitude": 93.509
        }
    ]
}
```

### 4.2 Data Models

#### 4.2.1 QueryInput
```python
class QueryInput(BaseModel):
    text: str
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Show me salinity profiles near the equator in March 2023"
            }
        }
```

#### 4.2.2 QueryResponse
```python
class QueryResponse(BaseModel):
    response: str
    
    class Config:
        schema_extra = {
            "example": {
                "response": "Based on the ARGO float data available..."
            }
        }
```

## 5. Configuration Management

### 5.1 Configuration File (`config/config.yaml`)
```yaml
database:
  postgresql:
    host: localhost
    port: 5432
    dbname: floatchat
    user: postgres
    password: 3303
  chromadb:
    host: localhost
    port: 8000

data:
  raw_path: data/raw/
  processed_path: data/processed/

llm:
  model: deepseek/deepseek-chat-v3.1:free
  api_key: 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

api:
  host: 0.0.0.0
  port: 8000

frontend:
  streamlit_port: 8501
```

### 5.2 Logging Configuration (`config/logging.conf`)
```ini
[loggers]
keys=root,src

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_src]
level=INFO
handlers=consoleHandler,fileHandler
qualname=src
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('floatchat.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 6. Error Handling

### 6.1 Error Types
```python
class FloatChatError(Exception):
    """Base exception for FloatChat"""
    pass

class DataIngestionError(FloatChatError):
    """Error during data ingestion"""
    pass

class LLMError(FloatChatError):
    """Error with LLM processing"""
    pass

class DatabaseError(FloatChatError):
    """Error with database operations"""
    pass

class ValidationError(FloatChatError):
    """Error with input validation"""
    pass
```

### 6.2 Error Handling Strategy
```python
def handle_api_error(func):
    """Decorator for API error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail="Database error")
        except LLMError as e:
            raise HTTPException(status_code=500, detail="LLM processing error")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
```

## 7. Testing Strategy

### 7.1 Unit Tests
```python
# Test RAG Pipeline
def test_rag_pipeline():
    """Test RAG pipeline functionality"""
    - Setup test data
    - Create RAG chain
    - Execute test query
    - Verify response format
    - Check SQL query extraction

# Test Data Ingestion
def test_data_ingestion():
    """Test ARGO data ingestion"""
    - Mock argopy responses
    - Test data processing
    - Verify output format
    - Check error handling

# Test API Endpoints
def test_chat_endpoint():
    """Test chat API endpoint"""
    - Send test query
    - Verify response structure
    - Check error responses
    - Validate status codes
```

### 7.2 Integration Tests
```python
def test_end_to_end_workflow():
    """Test complete workflow"""
    - Ingest test data
    - Extract metadata
    - Initialize vector DB
    - Send chat query
    - Verify response
    - Check dashboard functionality
```

## 8. Performance Optimization

### 8.1 Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_llm_instance(model_type: str) -> LLM:
    """Cache LLM instances"""
    return get_llm(model_type)

@lru_cache(maxsize=256)
def load_metadata() -> pd.DataFrame:
    """Cache metadata loading"""
    return pd.read_csv("data/processed/metadata.csv")
```

### 8.2 Database Optimization
```python
# ChromaDB optimization
def optimize_chromadb():
    """Optimize ChromaDB performance"""
    - Use persistent client
    - Configure embedding function
    - Set appropriate collection parameters
    - Implement connection pooling
```

## 9. Security Implementation

### 9.1 API Security
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_api_key(token: str = Depends(security)):
    """Verify API key"""
    if token.credentials != "valid_api_key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

### 9.2 Input Validation
```python
from pydantic import BaseModel, validator

class QueryInput(BaseModel):
    text: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 1000:
            raise ValueError('Query too long')
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
```

## 10. Monitoring and Logging

### 10.1 Structured Logging
```python
import structlog

logger = structlog.get_logger()

def log_query_execution(query: str, response: str, duration: float):
    """Log query execution details"""
    logger.info(
        "query_executed",
        query=query,
        response_length=len(response),
        duration_ms=duration * 1000,
        timestamp=datetime.utcnow().isoformat()
    )
```

### 10.2 Metrics Collection
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('floatchat_queries_total', 'Total number of queries')
query_duration = Histogram('floatchat_query_duration_seconds', 'Query duration')

def track_query_metrics(func):
    """Decorator to track query metrics"""
    def wrapper(*args, **kwargs):
        query_counter.inc()
        with query_duration.time():
            return func(*args, **kwargs)
    return wrapper
```

---

**Document Status**: Draft v1.0  
**Next Review**: October 2024  
**Approval**: Pending technical review
