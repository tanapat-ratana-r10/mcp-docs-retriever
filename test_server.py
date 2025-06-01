"""Manual smoke‑test for MCP Docs Server.

Steps performed:

1. Crawls *https://ai.pydantic.dev* (home page of Pydantic’s AI docs) using the
   `add_documentation` tool (crawler mode).
2. Asserts that at least one chunk was added to Qdrant.
3. Queries the corpus with `search_documentation` for the keyword *pydantic* and
   asserts that at least one hit is returned.

Run inside the same virtual‑env where you installed the package:

    python test_server.py

You must have Qdrant running on localhost:6333 beforehand.
"""

from __future__ import annotations

import sys
import time
from pprint import pprint

from server import (
    AddDocumentationArgs,
    SearchDocumentationArgs,
    add_documentation_tool,
    search_documentation_tool,
)

ENTRYPOINT_URL = "https://ai.pydantic.dev/"
PREFIX = "https://ai.pydantic.dev"  # restrict crawl
QUERY = "pydantic"  # simple keyword that should exist in the docs


def main() -> None:
    # ──────────────────────────────────────
    # 1. Ingest documentation via crawler
    # ──────────────────────────────────────
    print("Ingesting documentation from", ENTRYPOINT_URL)
    add_args = AddDocumentationArgs(entrypoint_url=ENTRYPOINT_URL, prefix=PREFIX)
    add_result = add_documentation_tool(add_args)
    pprint(add_result)

    chunks_added = add_result.get("chunks_added", 0)
    assert chunks_added > 0, "No chunks were ingested – crawl failed?"
    print(f"✅ Ingested {chunks_added} chunks from {add_result['pages_crawled']} pages\n")

    # give Qdrant a moment to finish indexing (usually immediate)
    time.sleep(1)

    # ──────────────────────────────────────
    # 2. Semantic search
    # ──────────────────────────────────────
    print(f"Searching for '{QUERY}' (top‑k=3)…")
    search_args = SearchDocumentationArgs(query=QUERY, top_k=3)
    search_result = search_documentation_tool(search_args)
    pprint(search_result)

    hits = search_result.get("results", [])
    assert hits, "Search returned zero hits – ingestion or search failed"
    print(f"✅ Search returned {len(hits)} results. Smoke‑test passed.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as err:
        print("❌ Test failed:", err, file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print("❌ Unexpected error:", exc, file=sys.stderr)
        sys.exit(1)
