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

if __name__ == "__main__":
    from src.data_ingestion.metadata_extractor import extract_metadata
    metadata = extract_metadata()
    init_vector_db(metadata)