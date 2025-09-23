from sentence_transformers import SentenceTransformer
from src.utils.logging import get_logger

logger = get_logger(__name__)

def get_embeddings(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    logger.info("Generated embeddings")
    return embeddings