# FloatChat Architecture

## Overview
FloatChat processes ARGO NetCDF data, stores it in PostgreSQL and ChromaDB, uses LangChain for RAG-based query processing, and serves results via a FastAPI backend and Streamlit frontend.

## Data Flow
1. **Ingestion**: `argopy` fetches ARGO data, converted to Parquet/SQL.
2. **Storage**: Relational data in PostgreSQL, metadata embeddings in ChromaDB.
3. **Query Processing**: User queries are translated to SQL via RAG (LangChain + Mock LLM).
4. **Visualization**: Streamlit renders chat responses and Plotly/Folium visualizations.

## Extensibility
- Add new data sources in `data_ingestion/`.
- Update RAG prompts in `llm/rag_pipeline.py`.