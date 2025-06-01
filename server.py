from typing import Optional, List
from pydantic import HttpUrl
from mcp.server.fastmcp import FastMCP
from docs_db import DocumentationDB
from scraper import DocumentationScraper

mcp = FastMCP("docs-retriever")
db = DocumentationDB()

@mcp.tool()
async def add_documentation(
    url: HttpUrl,
    max_pages: Optional[int] = 100,
    allowed_domains: Optional[List[str]] = None
) -> dict:
    """
    Add documentation by scraping all links under the entrypoint URL and storing the content in the vector database.
    """
    async with DocumentationScraper(
        base_url=str(url),
        allowed_domains=allowed_domains
    ) as scraper:
        pages = await scraper.scrape_all(max_pages=max_pages)
        stored_docs = []
        for page in pages:
            doc_id = db.add_document(
                content=page["content"],
                metadata={
                    "url": page["url"],
                    "title": page["title"],
                    **page["metadata"]
                }
            )
            stored_docs.append({
                "id": doc_id,
                "url": page["url"],
                "title": page["title"]
            })
        return {
            "status": "success",
            "pages_scraped": len(stored_docs),
            "documents": stored_docs
        }

@mcp.tool()
async def search_documentation(query: str, num_results: Optional[int] = 5) -> dict:
    """
    Search documentation using semantic search.
    """
    results = db.search_documents(query, n_results=num_results)
    return {
        "status": "success",
        "num_results": len(results),
        "results": [    
            {
                "id": doc["id"],
                "url": doc["metadata"].get("url"),
                "title": doc["metadata"].get("title"),
                "content": doc["content"],
                "score": 1 - doc["distance"]
            }
            for doc in results
        ]
    }

if __name__ == "__main__":
    mcp.run() 