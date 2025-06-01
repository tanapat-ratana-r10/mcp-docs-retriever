# mcp-docs-retriever

An MCP (Model Context Protocol) server that provides documentation retrieval capabilities similar to Cursor's `@docs` feature.

## Features

- **Add Documentation**: Add documentation from URLs with automatic crawling of subpages
- **Search Documentation**: Natural language search across all stored documentation
- **Web Scraping**: Automatically discovers and indexes all pages under a domain
- **Vector Search**: Uses HuggingFace embeddings for semantic search capabilities

## Installation

Using `uv`:

```bash
uv sync
```

## Usage

Run the MCP server:

```bash
uv run python main.py
```

## Available Tools

### 1. `add_documentation`
Add documentation from a URL with optional crawling of subpages.

Parameters:
- `url` (required): The URL to add/scrape documentation from
- `scrape_subpages` (optional, default=True): Whether to crawl and index all subpages
- `max_depth` (optional, default=2): How many levels deep to crawl
- `max_pages` (optional, default=50): Maximum number of pages to scrape
- `tags` (optional): List of tags for categorization

Examples:
```python
# Add a single page
await add_documentation(
    url="https://docs.python.org/3/library/asyncio.html",
    scrape_subpages=False,
    tags=["python", "asyncio"]
)

# Scrape entire documentation site
await add_documentation(
    url="https://ai.pydantic.dev",
    scrape_subpages=True,
    max_depth=2,
    max_pages=100,
    tags=["pydantic", "ai"]
)
```

### 2. `search_documentation`
Search the documentation using natural language queries.

Parameters:
- `query` (required): Natural language search query
- `limit` (optional, default=5): Number of results to return

Example:
```python
results = search_documentation("how to use async functions", limit=10)
```

## Architecture

The server is organized into modular components:

- `server.py`: MCP server with tool definitions
- `storage.py`: ChromaDB storage with vector embeddings
- `embeddings.py`: HuggingFace sentence transformer embeddings
- `scraper.py`: Web scraping and URL discovery utilities

## Storage

Documentation is stored locally using ChromaDB with vector embeddings for semantic search. The database is persisted at `~/.mcp-docs-retriever/chroma/`.

## Configuration

The server uses the following defaults:
- Embedding Model: `all-MiniLM-L6-v2` (from HuggingFace)
- Storage Location: `~/.mcp-docs-retriever/`
- Scraping Delay: 0.5 seconds between pages (to be respectful)

## MCP Integration

To use this server with an MCP client, add it to your MCP configuration:

```json
{
  "servers": {
    "docs-retriever": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp-docs-retriever/main.py"]
    }
  }
}
```