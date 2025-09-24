# 🌊 FloatChat - AI-Powered ARGO Ocean Data Discovery

**Problem Statement ID:** 25040  
**Organization:** Ministry of Earth Sciences (MoES)  
**Department:** Indian National Centre for Ocean Information Services (INCOIS)

## 📋 Overview

FloatChat is an AI-powered conversational interface for ARGO ocean data discovery and visualization. It democratizes access to complex oceanographic data by enabling natural language queries and interactive visualizations.

## 🎯 Key Features

### ✅ **Completed Features**

- **🌊 ARGO Data Ingestion**: Complete NetCDF processing pipeline
- **🧠 AI-Powered Chat**: Natural language querying with OpenRouter/DeepSeek
- **🗺️ Interactive Visualizations**: Geospatial maps, depth profiles, comparisons
- **📊 Data Export**: CSV and Parquet export capabilities
- **🔍 Vector Search**: ChromaDB for intelligent metadata retrieval
- **📱 Modern UI**: React-based dashboard and chat interface (Vite + React)

### 🔄 **In Progress**

- **SQL Query Generation**: Natural language to SQL translation
- **Extensibility**: BGC, glider, and buoy data integration

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenRouter API key (for DeepSeek model)

### Installation

1. **Clone and Setup**
```bash
git clone <repository>
cd FloatChat
pip install -e .
```

2. **Configure API**
```bash
# Update config/config.yaml with your OpenRouter API key
llm:
  model: deepseek/deepseek-chat-v3.1:free
  api_key: your_openrouter_api_key_here
```

3. **Run Data Ingestion**
```bash
python src/data_ingestion/ingest_argo.py
python src/data_ingestion/metadata_extractor.py
```

4. **Start Services**
```bash
# Terminal 1: Start API (FastAPI)
python src\api\main.py

# Terminal 2: Start React Frontend (Vite)
cd frontend
npm install
npm run dev
```

## 💬 Example Queries

The system handles complex oceanographic queries like:

- *"Show me salinity profiles near the equator in March 2023"*
- *"Compare BGC parameters in the Arabian Sea for the last 6 months"*
- *"What are the nearest ARGO floats to this location?"*
- *"Find floats operating in the Bay of Bengal region"*

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    React        │    │   FastAPI       │    │   ChromaDB      │
│   Frontend      │◄──►│   Backend       │◄──►│   Vector DB     │
│ (Vite + UI)     │    │   (RAG Pipeline)│    │   (Metadata)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenRouter    │
                       │   (DeepSeek)    │
                       └─────────────────┘
```

## 📊 Data Pipeline

1. **Ingestion**: ARGO NetCDF → Structured Data (Parquet)
2. **Metadata**: Extract summaries → ChromaDB vector storage
3. **Query**: Natural language → RAG pipeline → LLM response
4. **Visualization**: Interactive maps and profiles

## 🗂️ Project Structure

```
FloatChat/
├── src/
│   ├── api/                 # FastAPI backend
│   ├── data_ingestion/      # ARGO data processing
│   ├── database/            # ChromaDB integration
│   ├── llm/                 # RAG pipeline & models
│   └── utils/               # Logging & utilities
├── frontend/                # React UI (Vite)
├── config/                  # Configuration files
├── data/                    # Processed data storage
└── docs/                    # Documentation
```

## 🎨 Visualizations

### Interactive Dashboard Features:
- **🗺️ Map View**: ARGO float locations with trajectories
- **📈 Depth Profiles**: Temperature-depth-time visualizations
- **🔬 Comparisons**: Multi-float salinity comparisons
- **📊 Data Export**: Download capabilities

## 🔧 Configuration

### Environment Variables
```bash
OPENROUTER_API_KEY=your_key_here
LLM_TYPE=openrouter  # Optional override
```

### Data Sources
- **Primary**: Indian Ocean ARGO floats
- **Format**: NetCDF → Parquet conversion
- **Coverage**: Temperature, Salinity, Pressure profiles

## 🚀 Future Enhancements

- **BGC Integration**: Bio-Geo-Chemical float data
- **Glider Support**: Autonomous underwater vehicle data
- **Buoy Integration**: Surface buoy observations
- **NetCDF Export**: Full oceanographic standard compliance
- **Real-time Updates**: Live data streaming

## 📈 Performance

- **Response Time**: < 2 seconds for typical queries
- **Data Scale**: Handles thousands of ARGO profiles
- **Accuracy**: Context-aware responses with metadata validation

## 🤝 Contributing

This system was developed for the Smart India Hackathon 2025 under Problem Statement 25040.

## 📄 License

Developed for Ministry of Earth Sciences (MoES) - INCOIS

---

**Built with ❤️ for Ocean Science** 🌊

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000