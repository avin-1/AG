from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever, Document
from pydantic import Field
from src.database.vector_db import init_vector_db
from src.llm.models import get_llm
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChromaRetriever(BaseRetriever):
    """Custom retriever that directly uses ChromaDB collection"""
    
    collection: object = Field(exclude=True)  # Exclude from serialization
    
    def get_relevant_documents(self, query: str):
        """Retrieve relevant documents from ChromaDB"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                for doc in results['documents'][0]:
                    documents.append(Document(page_content=doc))
            
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


def setup_rag(metadata, llm_type="mock"):
    # Step 1: Initialize ChromaDB collection
    collection = init_vector_db(metadata)

    # Step 2: Create custom retriever
    retriever = ChromaRetriever(collection=collection)

    # Step 3: Get LLM instance
    llm = get_llm(model_type=llm_type)

    # Step 4: Define enhanced prompt template for ARGO data queries with SQL generation
    prompt_template = """
    You are FloatChat, an AI-powered ocean data assistant specializing in ARGO float data analysis for the Indian Ocean region.
    You help users discover, query, and visualize oceanographic data through natural language.

    ARGO Float Context:
    {context}

    User Question: {question}

    Instructions for answering ocean data queries:
    
    For location-based queries (e.g., "near the equator", "Arabian Sea"):
    - Identify relevant latitude/longitude ranges from the context
    - List specific float IDs in those regions
    - Provide geographic context (e.g., "Arabian Sea region: 10°N-25°N, 50°E-80°E")
    
    For temporal queries (e.g., "March 2023", "last 6 months"):
    - Extract time ranges from the context
    - Identify floats active during those periods
    - Provide specific date ranges when available
    
    For parameter queries (e.g., "salinity profiles", "temperature", "BGC parameters"):
    - Explain what parameters are available (TEMP, PSAL, PRES)
    - Note that BGC parameters may not be available in current dataset
    - Suggest visualization approaches
    
    For comparison queries (e.g., "compare", "nearest floats"):
    - Identify relevant floats for comparison
    - Suggest specific float IDs and their characteristics
    - Recommend using the dashboard for detailed comparisons
    
    Always:
    - Be specific with float IDs, coordinates, and time ranges
    - Suggest using the dashboard for detailed visualizations
    - Mention data limitations when relevant
    - Provide actionable next steps for data exploration

    Additionally, generate a SQL query that would retrieve the relevant data from a hypothetical ARGO database.
    The database schema includes tables like:
    - argo_floats (platform_number, latitude, longitude, time)
    - argo_profiles (platform_number, pressure, temperature, salinity, time)
    
    Format your response as:
    
    **SQL Query:**
    ```sql
    [Your generated SQL query here]
    ```
    
    **Answer:**
    [Your detailed response here]

    Answer:
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


def run_rag_query(chain, question):
    result = chain.invoke({"query": question})
    
    # Extract SQL query from the response
    response_text = result["result"]
    sql_query = extract_sql_query(response_text)
    
    # Log the SQL query to terminal
    if sql_query:
        logger.info("=" * 80)
        logger.info("🔍 GENERATED SQL QUERY:")
        logger.info("=" * 80)
        logger.info(sql_query)
        logger.info("=" * 80)
    else:
        logger.info("⚠️  No SQL query generated for this question")
    
    logger.info(f"RAG question: {question}")
    logger.info(f"RAG response: {response_text}")
    
    return response_text


def extract_sql_query(response_text):
    """Extract SQL query from the LLM response"""
    import re
    
    # Look for SQL query in code blocks
    sql_pattern = r'```sql\s*(.*?)\s*```'
    match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    # Look for SQL query after "SQL Query:" marker
    sql_pattern2 = r'\*\*SQL Query:\*\*\s*```sql\s*(.*?)\s*```'
    match2 = re.search(sql_pattern2, response_text, re.DOTALL | re.IGNORECASE)
    
    if match2:
        return match2.group(1).strip()
    
    return None