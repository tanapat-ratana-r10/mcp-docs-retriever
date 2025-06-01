# MCP Documentation Server

A Model Context Protocol (MCP) server that provides tools for scraping, managing, and searching documentation using a vector database.

## Setup

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Run the server:
```bash
python server.py
```

The server will start on `http://localhost:8000`.

## Features

- `add_documentation` tool: Scrape documentation from a URL and store it in the vector database
  - Parameters:
    - `url`: The entry point URL to start scraping from
    - `max_pages`: Maximum number of pages to scrape (default: 100)
    - `allowed_domains`: List of allowed domains to scrape (default: same as entry URL)
- `search_documentation` tool: Search documentation using semantic search
  - Parameters:
    - `query`: The search query
    - `num_results`: Number of results to return (default: 5)

## Implementation Details

- Uses ChromaDB as the vector database
- Employs sentence-transformers for document embeddings
- Stores documents with metadata including source URL and title
- Supports semantic search
- Uses BeautifulSoup4 for HTML parsing and content extraction
- Implements async scraping with aiohttp for better performance
- Filters out non-documentation content (images, PDFs, etc.)
- Respects robots.txt and domain restrictions
- **Note:** The `DocumentationDB` methods (`add_document`, `search_documents`) are synchronous and should be called without `await`.

## Example Usage

You can test the tools directly by importing them from `server.py`:

```python
import asyncio
from server import add_documentation, search_documentation

async def test_docs_retriever():
    # Add documentation (scrape and store)
    result = await add_documentation(
        url="https://ai.pydantic.dev",
        max_pages=5
    )
    print(f"Add documentation result: {result}")

    # Search documentation (semantic search)
    search_result = await search_documentation(
        query="What is PydanticAI?",
        num_results=3
    )
    print(f"Search result: {search_result}")

if __name__ == "__main__":
    asyncio.run(test_docs_retriever())
```

## Notes
- The tools in `server.py` are async because they use async scraping, but the database operations are synchronous.
- Do not use `await` with `db.add_document` or `db.search_documents`.
- For MCP client usage, see the [MCP documentation](https://modelcontextprotocol.io/llms-full.txt).