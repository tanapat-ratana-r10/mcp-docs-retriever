from typing import Optional
from mcp.server.fastmcp import FastMCP
from storage import add_documentation_from_url, query_documentation

# Initialize FastMCP server
mcp = FastMCP("mcp-docs-retriever")

@mcp.tool()
def add_documentation_tool(entrypoint_url: str) -> str:
    """
    Add a documentation entry to the semantic search database by crawling and chunking the content at the entrypoint_url.

    Args:
        entrypoint_url: The URL to crawl and index
    """
    doc_id = entrypoint_url  # Use the URL as the unique doc_id
    add_documentation_from_url(doc_id, entrypoint_url)
    return f"Document from '{entrypoint_url}' added and indexed successfully."

@mcp.tool()
def search_documentation(query: str, n_results: int = 3) -> list[str]:
    """
    Search the indexed documentation using a natural language query.

    Args:
        query: The search query
        n_results: Number of results to return (default: 3)
    Returns:
        List of relevant documentation chunks as strings
    """
    results = query_documentation(query, n_results)
    # Extract and return the document texts
    return results.get("documents", [[]])[0]

if __name__ == "__main__":
    mcp.run(transport="stdio")
