"""storage.py – Qdrant helper layer
=================================
This module abstracts **all persistence** for the MCP Docs Server.  It offers
just two public functions:

* `add_documentation(title, content, metadata=None)` – split & embed text, then
  upsert into Qdrant, returning point IDs.
* `search_documentation(query, top_k=5, filters=None)` – ANN search with
  optional exact‐match payload filters.

**Connection modes**
--------------------
Set an environment variable `QDRANT_MODE` to choose how we create the client:

| `QDRANT_MODE` | Client Factory                                       | When to use                           |
|---------------|------------------------------------------------------|---------------------------------------|
| *(default)*   | `QdrantClient(host, port)`                           | Docker / native server on 6333        |
| `memory`      | `QdrantClient(location=":memory:")`                  | Unit tests, throwaway sessions        |
| `local`       | `QdrantClient(path=$QDRANT_PATH or "./qdrant_data")` | Persistent dev DB, no extra process   |

No other code needs to change – the same collection name works in every mode.

Requirements
------------
```
pip install qdrant-client sentence-transformers lxml bs4 html2text
```

Usage example
-------------
```python
from storage import add_documentation, search_documentation

add_documentation(
    title="Getting Started",
    content="# Hello World\nThis is a test…",
    metadata={"repo": "demo"},
)
print(search_documentation("hello world"))
```
"""

from __future__ import annotations

import os
import textwrap
from typing import Any, Dict, List
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────
# Connection parameters (can be tweaked via environment)
# ──────────────────────────────────────────────────────────

QDRANT_MODE = os.getenv("QDRANT_MODE", "remote").lower()  # remote | memory | local
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_data")

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "documentation")
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
CHUNK_MAX_TOKENS = int(os.getenv("CHUNK_MAX_TOKENS", "256"))

# ──────────────────────────────────────────────────────────
# Instantiate Qdrant client according to mode
# ──────────────────────────────────────────────────────────

if QDRANT_MODE == "memory":
    _client = QdrantClient(location=":memory:")
elif QDRANT_MODE == "local":
    _client = QdrantClient(path=QDRANT_PATH)
else:  # remote (default)
    _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# One embedding model shared by all calls (thread-safe)
_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
_VECTOR_DIM = _model.get_sentence_embedding_dimension()

# ──────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────

def _ensure_collection() -> None:
    """Create the Qdrant collection if it does not already exist."""

    if _client.collection_exists(COLLECTION_NAME):
        return

    _client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=rest.VectorParams(size=_VECTOR_DIM, distance=rest.Distance.COSINE),
        replication_factor=1,
    )


def _chunk_text(text: str, max_tokens: int = CHUNK_MAX_TOKENS) -> List[str]:
    """Very naive splitter: wraps text every *max_tokens* words.

    Good enough for a demo; swap with tiktoken or LangChain later.
    """
    return [part.strip() for part in textwrap.wrap(text, width=max_tokens * 5) if part.strip()]

# ──────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────

def add_documentation(
    *,
    title: str,
    content: str,
    metadata: Dict[str, Any] | None = None,
) -> List[str]:
    """Embed *content* and upsert into Qdrant.  Returns list of point IDs."""

    _ensure_collection()
    metadata = metadata or {}

    chunks = _chunk_text(content)
    vectors = _model.encode(chunks, normalize_embeddings=True).tolist()

    payloads: List[dict] = []
    ids: List[str] = []
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        payloads.append(
            {
                "title": title,
                "text": chunk,
                "chunk_index": idx,
                **metadata,
            }
        )
        ids.append(str(uuid4()))

    _client.upsert(
        collection_name=COLLECTION_NAME,
        points=rest.Batch(ids=ids, vectors=vectors, payloads=payloads),
    )
    return ids


def search_documentation(
    query: str,
    *,
    top_k: int = 5,
    filters: Dict[str, Any] | None = None,
) -> List[dict]:
    """Return the *top_k* most similar payloads for *query*."""

    _ensure_collection()
    query_vec = _model.encode(query, normalize_embeddings=True).tolist()

    filter_obj = None
    if filters:
        conditions = [
            rest.FieldCondition(key=k, match=rest.MatchValue(value=v)) for k, v in filters.items()
        ]
        filter_obj = rest.Filter(must=conditions)

    hits = _client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec,
        query_filter=filter_obj,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            **(hit.payload or {}),
        }
        for hit in hits
    ]

# Exported names for star-imports
__all__ = ["add_documentation", "search_documentation"]