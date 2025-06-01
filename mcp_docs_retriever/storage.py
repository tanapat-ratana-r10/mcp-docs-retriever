import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class DocumentStorage:
    def __init__(self, storage_path: Path):
        self.client = chromadb.PersistentClient(
            path=str(storage_path / "chroma"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use ChromaDB's built-in sentence transformer
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="documentation",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_function
        )
    
    def add_document(self, title: str, content: str, url: str = None, tags: list[str] = None) -> str:
        """Add a single document to the collection."""
        doc_id = f"doc_{self.collection.count() + 1}"
        
        metadata = {
            "title": title,
            "tags": json.dumps(tags) if tags else "[]"
        }
        if url:
            metadata["url"] = url
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search documents using natural language query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        if not results['documents'][0]:
            return []
        
        formatted_results = []
        for i in range(len(results['documents'][0])):
            doc = {
                "content": results['documents'][0][i][:500] + "...",  # Truncate for readability
                "metadata": results['metadatas'][0][i],
                "id": results['ids'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            }
            
            # Parse tags from JSON string
            if 'tags' in doc['metadata']:
                doc['metadata']['tags'] = json.loads(doc['metadata']['tags'])
                
            formatted_results.append(doc)
        
        return formatted_results