from fastapi import APIRouter
from src.llm.rag_pipeline import setup_rag, run_rag_query
from src.data_ingestion.metadata_extractor import extract_metadata
from src.api.schema import QueryInput, QueryResponse
from src.utils.logging import get_logger
import os
import yaml

router = APIRouter()
logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config/config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

@router.post("/query", response_model=QueryResponse)
async def chat_query(query: QueryInput):
    # Get LLM type from config.yaml or environment
    config = load_config()
    llm_type = os.getenv("LLM_TYPE") or config.get("llm", {}).get("model", "mock")
    
    # Map config model names to our LLM types
    # Check for OpenRouter API key format first (sk-or- prefix)
    api_key = config.get("llm", {}).get("api_key", "")
    if api_key.startswith("sk-or-"):
        llm_type = "openrouter"
    elif api_key.startswith("hf_"):
        llm_type = "huggingface"
    elif "openrouter" in llm_type.lower() or "deepseek" in llm_type.lower():
        llm_type = "openrouter"
    elif "huggingface" in llm_type.lower() or "hf_" in llm_type.lower():
        llm_type = "huggingface"
    elif "openai" in llm_type.lower() and not api_key.startswith("hf_"):
        llm_type = "openai"
    elif "anthropic" in llm_type.lower():
        llm_type = "anthropic"
    else:
        llm_type = "mock"
    
    logger.info(f"Using LLM type: {llm_type}")
    
    metadata = extract_metadata()
    rag_chain = setup_rag(metadata, llm_type=llm_type)
    response = run_rag_query(rag_chain, query.text)
    return QueryResponse(response=response)