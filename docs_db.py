import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
import uuid

class DocumentationDB:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="documentation",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        doc_id = str(uuid.uuid4())
        embedding = self.embedding_model.encode(content).tolist()
        
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id

    def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return [
            {
                "id": id,
                "content": doc,
                "metadata": meta,
                "distance": dist
            }
            for id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ] 