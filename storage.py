import os
os.environ["CHROMA_EMBEDDING_ONNX_DISABLE_COREML"] = "1"

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import Optional, List
import requests
from bs4 import BeautifulSoup

# Initialize ChromaDB client (using local persistent storage)
chroma_client = chromadb.Client(Settings(persist_directory=".chroma_db"))

# Use SentenceTransformers embedding model (all-MiniLM-L6-v2)
default_embedder = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create or get a collection for documentation, always using the embedding function
collection = chroma_client.get_or_create_collection(
    "documentation",
    embedding_function=default_embedder
)

def add_documentation(doc_id: str, content: str, metadata: Optional[dict] = None):
    """
    Add a documentation entry to the ChromaDB collection.
    :param doc_id: Unique identifier for the document
    :param content: The text content of the documentation
    :param metadata: Optional metadata dictionary
    """
    embedding = default_embedder([content])[0]
    collection.add(
        ids=[doc_id],
        documents=[content],
        embeddings=[embedding],
        metadatas=[metadata or {}]
    )

def query_documentation(query: str, n_results: int = 3):
    """
    Query documentation using semantic search.
    :param query: Natural language query
    :param n_results: Number of results to return
    :return: List of matching documents
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results

def fetch_and_chunk_url(url: str, chunk_size: int = 1000) -> List[str]:
    """
    Fetches the content at the given URL and splits it into text chunks.
    :param url: The URL to fetch
    :param chunk_size: The max size of each chunk (in characters)
    :return: List of text chunks
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Extract visible text
    text = ' '.join(soup.stripped_strings)
    # Chunk the text
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

def add_documentation_from_url(doc_id: str, url: str, metadata: Optional[dict] = None):
    """
    Fetch, chunk, and add documentation from a URL to ChromaDB.
    :param doc_id: Unique identifier for the document
    :param url: The URL to fetch and index
    :param metadata: Optional metadata dictionary
    """
    chunks = fetch_and_chunk_url(url)
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx}"
        chunk_metadata = dict(metadata or {})
        chunk_metadata.update({"url": url, "chunk_index": idx})
        add_documentation(chunk_id, chunk, chunk_metadata)
