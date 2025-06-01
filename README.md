# MCP Docs Retriever

This project is an MCP (Model Context Protocol) server for adding and retrieving documentation with semantic search using ChromaDB.

## Setup (using uv)

1. Install [uv](https://github.com/astral-sh/uv) if you haven't already:

    curl -Ls https://astral.sh/uv/install.sh | sh

2. Create a virtual environment and install dependencies:

    uv venv
    uv pip install chromadb
    uv pip install "mcp[cli]" httpx

3. Activate the virtual environment:

    source .venv/bin/activate

## Running the MCP Server

To start the server:

    uv run server.py

The server exposes the `add_documentation` tool for MCP clients.

---

For more information on ChromaDB, see: https://docs.trychroma.com/
For more information on MCP, see: https://modelcontextprotocol.io/quickstart/server