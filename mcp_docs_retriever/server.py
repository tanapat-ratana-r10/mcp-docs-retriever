from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP

from .storage import DocumentStorage
from .scraper import scrape_documentation_site

STORAGE_PATH = Path.home() / ".mcp-docs-retriever"
STORAGE_PATH.mkdir(exist_ok=True)

mcp = FastMCP("mcp-docs-retriever")
storage = DocumentStorage(STORAGE_PATH)


@mcp.tool()
async def add_documentation(
    url: str,
    scrape_subpages: bool = True,
    max_depth: int = 2,
    max_pages: int = 50,
    tags: Optional[list[str]] = None
) -> str:
    """
    Add documentation from a URL. If scrape_subpages is True, it will crawl and index all pages under the domain.
    
    Args:
        url: The URL to add/scrape documentation from
        scrape_subpages: Whether to scrape all subpages (default: True)
        max_depth: How many levels deep to crawl (default: 2)
        max_pages: Maximum number of pages to scrape (default: 50)
        tags: Optional tags to add to the documentation
    """
    if scrape_subpages:
        # Scrape entire documentation site
        pages = await scrape_documentation_site(url, max_depth, max_pages)
        
        if not pages:
            return f"Failed to scrape any pages from {url}"
        
        # Add all scraped pages
        added_count = 0
        for page in pages:
            doc_tags = tags or []
            doc_tags.extend(["scraped", page["domain"]])
            
            storage.add_document(
                title=page["title"],
                content=page["content"],
                url=page["url"],
                tags=doc_tags
            )
            added_count += 1
        
        return f"Successfully scraped and indexed {added_count} pages from {url}"
    else:
        # Just add the single URL
        from .scraper import scrape_url
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            title, content = await scrape_url(url, client)
            
            if content.startswith("Failed to scrape:"):
                return content
            
            doc_id = storage.add_document(
                title=title,
                content=content,
                url=url,
                tags=tags
            )
            
            return f"Successfully added documentation '{title}' with ID: {doc_id}"


@mcp.tool()
def search_documentation(
    query: str,
    limit: int = 5
) -> list[dict]:
    """
    Search documentation using natural language query.
    
    Args:
        query: Natural language search query
        limit: Number of results to return (default: 5)
    
    Returns:
        List of search results with content, metadata, and relevance scores
    """
    return storage.search(query, limit)