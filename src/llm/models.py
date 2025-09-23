from langchain.llms.base import LLM
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from src.utils.logging import get_logger
import os
import yaml

logger = get_logger(__name__)

class MockLLM(LLM):
    def _call(self, prompt, stop=None):
        logger.info(f"Mock LLM called with prompt: {prompt}")
        return "Mock response: SQL query generated"
    
    @property
    def _llm_type(self):
        return "mock"

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config/config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def get_llm(model_type="mock", **kwargs):
    """Get LLM instance based on type"""
    config = load_config()
    
    if model_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or config.get("llm", {}).get("api_key")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, falling back to MockLLM")
            return MockLLM()
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            api_key=api_key,
            **kwargs
        )
    elif model_type == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY") or config.get("llm", {}).get("api_key")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found, falling back to MockLLM")
            return MockLLM()
        return ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.1,
            api_key=api_key,
            **kwargs
        )
    elif model_type == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY") or config.get("llm", {}).get("api_key")
        model_name = config.get("llm", {}).get("model", "microsoft/DialoGPT-medium")
        
        if not api_key:
            logger.warning("HUGGINGFACE_API_KEY not found, falling back to MockLLM")
            return MockLLM()
        
        # Use a simpler HuggingFace approach
        llm = HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=api_key,
            **kwargs
        )
        
        return llm
    elif model_type == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY") or config.get("llm", {}).get("api_key")
        model_name = config.get("llm", {}).get("model", "deepseek/deepseek-chat-v3.1:free")
        
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not found, falling back to MockLLM")
            return MockLLM()
        
        # Use OpenRouter with OpenAI-compatible API
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            **kwargs
        )
    else:
        return MockLLM()