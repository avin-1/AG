# FloatChat - High-Level Design (HLD) Document

## Document Information
- **Project**: FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data Discovery
- **Version**: 1.0
- **Date**: September 2024
- **Approach**: Retrieval-Augmented Generation (RAG)
- **Organization**: Ministry of Earth Sciences (MoES) - INCOIS

## 1. Executive Summary

FloatChat is an AI-powered conversational system that enables users to query, explore, and visualize ARGO float oceanographic data using natural language. The system leverages Retrieval-Augmented Generation (RAG) to bridge the gap between complex oceanographic data and intuitive user interactions.

## 2. System Overview

### 2.1 Architecture Pattern
- **Pattern**: Microservices Architecture with RAG Pipeline
- **Style**: Event-driven, API-first design
- **Deployment**: Containerized (Docker) with horizontal scaling capability

### 2.2 Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   RAG Pipeline  │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (LangChain)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Data Layer    │    │   Vector DB     │
                       │   (PostgreSQL)  │    │   (ChromaDB)    │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Ingestion│
                       │   (Argopy)      │
                       └─────────────────┘
```

## 3. Functional Requirements

### 3.1 Core Features
- **Natural Language Querying**: Convert user questions to structured data queries
- **ARGO Data Ingestion**: Process NetCDF files into structured formats
- **Interactive Visualizations**: Geospatial maps, depth profiles, parameter comparisons
- **Conversational Interface**: Chat-based interaction with context awareness
- **Data Export**: Multiple format support (CSV, Parquet, NetCDF)

### 3.2 User Stories
1. **As an oceanographer**, I want to ask "Show me salinity profiles near the equator" and get relevant data
2. **As a researcher**, I want to compare BGC parameters across different regions
3. **As a student**, I want to explore ARGO float trajectories interactively
4. **As a decision maker**, I want to export data for further analysis

## 4. Non-Functional Requirements

### 4.1 Performance
- **Response Time**: < 3 seconds for natural language queries
- **Throughput**: Support 100+ concurrent users
- **Scalability**: Horizontal scaling capability
- **Availability**: 99.5% uptime

### 4.2 Security
- **Authentication**: API key-based authentication
- **Authorization**: Role-based access control
- **Data Privacy**: Encrypted data transmission
- **Audit Logging**: Comprehensive activity tracking

### 4.3 Reliability
- **Fault Tolerance**: Graceful degradation on component failures
- **Data Consistency**: ACID compliance for critical operations
- **Backup Strategy**: Automated daily backups
- **Disaster Recovery**: RTO < 4 hours, RPO < 1 hour

## 5. System Architecture

### 5.1 Component Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit Frontend  │  REST API  │  WebSocket (Future)        │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Chat Service  │  Query Service  │  Visualization Service        │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Business Logic Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  RAG Pipeline  │  Query Translator  │  Data Processor            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Data Access Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Vector DB     │  Relational DB  │  File Storage                │
│  (ChromaDB)    │  (PostgreSQL)   │  (Parquet/NetCDF)            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow Architecture
```
User Query → Natural Language Processing → Vector Search → LLM Processing → Response Generation
     │                    │                    │              │                    │
     ▼                    ▼                    ▼              ▼                    ▼
Frontend → API Gateway → RAG Pipeline → ChromaDB → LLM (OpenRouter) → Structured Response
```

## 6. Technology Stack

### 6.1 Frontend Technologies
- **Framework**: Streamlit
- **Visualization**: Plotly, Folium
- **UI Components**: Custom Streamlit components
- **State Management**: Streamlit session state

### 6.2 Backend Technologies
- **API Framework**: FastAPI
- **Web Server**: Uvicorn
- **Async Processing**: asyncio
- **Task Queue**: Celery (future)

### 6.3 Data Technologies
- **Vector Database**: ChromaDB
- **Relational Database**: PostgreSQL
- **Data Processing**: Pandas, Xarray
- **File Formats**: Parquet, NetCDF

### 6.4 AI/ML Technologies
- **LLM Framework**: LangChain
- **Embeddings**: Sentence Transformers
- **LLM Provider**: OpenRouter (DeepSeek)
- **RAG Pipeline**: Custom LangChain implementation

### 6.5 Infrastructure
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes (future)
- **Monitoring**: Prometheus, Grafana
- **Logging**: Structured logging with Python logging

## 7. Data Architecture

### 7.1 Data Sources
- **Primary**: ARGO NetCDF files via Argopy
- **Secondary**: Metadata from ARGO data centers
- **Future**: BGC floats, Gliders, Buoys

### 7.2 Data Processing Pipeline
```
Raw NetCDF → Data Ingestion → Data Cleaning → Feature Extraction → Vector Embeddings → Storage
     │              │              │              │                    │              │
     ▼              ▼              ▼              ▼                    ▼              ▼
Argopy API → Pandas/Xarray → Quality Control → Metadata → Sentence Transformers → ChromaDB
```

### 7.3 Data Models
- **ARGO Profiles**: Temperature, Salinity, Pressure measurements
- **Float Metadata**: Platform number, location, time ranges
- **User Queries**: Natural language questions and context
- **Responses**: Structured answers with SQL queries

## 8. Integration Architecture

### 8.1 External Integrations
- **ARGO Data**: Argopy library for data access
- **LLM Services**: OpenRouter API for model inference
- **Map Services**: OpenStreetMap for geospatial visualization
- **Future**: Satellite data APIs, Weather services

### 8.2 Internal Integrations
- **Service-to-Service**: RESTful APIs with JSON
- **Data Synchronization**: Event-driven updates
- **Cache Management**: Redis for session management
- **Message Queue**: RabbitMQ for async processing

## 9. Security Architecture

### 9.1 Authentication & Authorization
- **API Keys**: Secure key management
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: User permissions
- **Rate Limiting**: API protection

### 9.2 Data Security
- **Encryption**: TLS 1.3 for data in transit
- **Data Masking**: Sensitive information protection
- **Audit Trails**: Comprehensive logging
- **Compliance**: GDPR, data privacy regulations

## 10. Deployment Architecture

### 10.1 Environment Strategy
- **Development**: Local Docker containers
- **Staging**: Cloud-based testing environment
- **Production**: Kubernetes cluster with auto-scaling

### 10.2 CI/CD Pipeline
- **Source Control**: Git with feature branches
- **Build**: Docker image creation
- **Test**: Automated testing suite
- **Deploy**: Blue-green deployment strategy

## 11. Monitoring & Observability

### 11.1 Metrics
- **Performance**: Response times, throughput
- **Business**: Query success rates, user engagement
- **Infrastructure**: CPU, memory, disk usage
- **Application**: Error rates, latency percentiles

### 11.2 Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Centralized Logging**: ELK stack (Elasticsearch, Logstash, Kibana)
- **Alerting**: Real-time notifications for critical issues

## 12. Scalability Considerations

### 12.1 Horizontal Scaling
- **Stateless Services**: API and frontend services
- **Load Balancing**: Round-robin with health checks
- **Database Sharding**: Partition by geographic regions
- **Cache Distribution**: Redis cluster for session management

### 12.2 Performance Optimization
- **Caching Strategy**: Multi-level caching (Redis, CDN)
- **Database Optimization**: Indexing, query optimization
- **Async Processing**: Non-blocking I/O operations
- **Resource Management**: Connection pooling, memory optimization

## 13. Future Enhancements

### 13.1 Short-term (3-6 months)
- **Model Context Protocol (MCP)**: Enhanced tool integration
- **Real-time Data**: Live ARGO float data streaming
- **Advanced Visualizations**: 3D oceanographic plots
- **Mobile Support**: Responsive design optimization

### 13.2 Long-term (6-12 months)
- **Multi-modal LLMs**: Image and text processing
- **Satellite Integration**: Combined in-situ and remote sensing
- **Predictive Analytics**: Oceanographic forecasting
- **Collaborative Features**: Multi-user workspaces

## 14. Risk Assessment

### 14.1 Technical Risks
- **LLM Reliability**: Model accuracy and consistency
- **Data Quality**: ARGO data completeness and accuracy
- **Scalability**: Performance under high load
- **Integration**: Third-party service dependencies

### 14.2 Mitigation Strategies
- **Fallback Mechanisms**: Graceful degradation
- **Data Validation**: Quality assurance processes
- **Performance Testing**: Load testing and optimization
- **Service Monitoring**: Proactive issue detection

## 15. Success Metrics

### 15.1 Technical Metrics
- **Query Success Rate**: > 95%
- **Response Time**: < 3 seconds average
- **System Uptime**: > 99.5%
- **User Satisfaction**: > 4.5/5 rating

### 15.2 Business Metrics
- **User Adoption**: Monthly active users
- **Query Volume**: Daily query count
- **Data Coverage**: Geographic and temporal coverage
- **Feature Usage**: Most used functionalities

---

**Document Status**: Draft v1.0  
**Next Review**: October 2024  
**Approval**: Pending technical review
