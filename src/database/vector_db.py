import chromadb
from chromadb.utils import embedding_functions
from src.utils.logging import get_logger

logger = get_logger(__name__)

def init_vector_db(metadata):
    # Use the default embedding function (sentence-transformers)
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    # Create persistent client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get or create collection with embedding function
    try:
        collection = client.get_collection("argo_metadata")
        logger.info("Using existing ChromaDB collection")
    except:
        collection = client.create_collection(
            "argo_metadata",
            embedding_function=embedding_function
        )
        logger.info("Created new ChromaDB collection")
    
    # Add metadata as documents
    for idx, row in metadata.iterrows():
        doc = f"Float {row['PLATFORM_NUMBER']}: Lat {row['LATITUDE_min']}-{row['LATITUDE_max']}, Lon {row['LONGITUDE_min']}-{row['LONGITUDE_max']}, Time {row['TIME_min']}-{row['TIME_max']}"
        collection.add(documents=[doc], ids=[str(row['PLATFORM_NUMBER'])])
    
    logger.info("Initialized ChromaDB with metadata")
    return collection


def query_nearest_platforms(collection, query_text: str, n_results: int = 3) -> list[str]:
    """Return the nearest platform_number IDs from ChromaDB for a query string."""
    try:
        res = collection.query(query_texts=[query_text], n_results=n_results)
        ids = res.get("ids", [[]])[0]
        return [str(x) for x in ids]
    except Exception as e:
        logger.error(f"Chroma query failed: {e}")
        return []


def query_nearest_by_location(collection, lat: float, lon: float, n_results: int = 3) -> list[str]:
    """Approximate nearest platforms by location using metadata text and embedding proximity.

    We encode a simple text like "lat: {lat}, lon: {lon}" and rely on the
    metadata strings to be similar for nearby ranges.
    """
    try:
        q = f"lat: {lat:.4f}, lon: {lon:.4f}"
        res = collection.query(query_texts=[q], n_results=n_results)
        ids = res.get("ids", [[]])[0]
        return [str(x) for x in ids]
    except Exception as e:
        logger.error(f"Chroma location query failed: {e}")
        return []

if __name__ == "__main__":
    from src.data_ingestion.metadata_extractor import extract_metadata
    metadata = extract_metadata()
    init_vector_db(metadata)