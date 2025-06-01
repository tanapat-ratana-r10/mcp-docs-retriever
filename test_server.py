#!/usr/bin/env python
import asyncio
import sys
from mcp_docs_retriever.server import add_documentation, search_documentation


async def test_mcp_server():
    print("Testing MCP Documentation Server\n")
    
    # Test 1: Add a single documentation page
    print("1. Adding Pydantic AI documentation (single page)...")
    result = await add_documentation(
        url="https://ai.pydantic.dev",
        scrape_subpages=False,
        tags=["pydantic", "ai", "test"]
    )
    print(f"Result: {result}\n")
    
    # Test 2: Search for documentation
    print("2. Searching for 'pydantic' documentation...")
    results = search_documentation("pydantic", limit=3)
    
    if results:
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  - Title: {result['metadata'].get('title', 'No title')}")
            print(f"  - URL: {result['metadata'].get('url', 'No URL')}")
            print(f"  - Tags: {result['metadata'].get('tags', [])}")
            print(f"  - Content preview: {result['content'][:100]}...")
    else:
        print("No results found")
    
    # Test 3: Add documentation with subpages
    print("\n3. Adding Pydantic AI documentation (with subpages)...")
    print("This may take a while as it scrapes multiple pages...")
    result = await add_documentation(
        url="https://ai.pydantic.dev",
        scrape_subpages=True,
        max_depth=2,  # Moderate depth to find good amount of pages
        max_pages=20,  # Reasonable limit for testing
        tags=["pydantic-ai", "documentation"]
    )
    print(f"Result: {result}\n")
    
    # Test 4: Search with more specific query
    print("4. Searching for 'agents' in documentation...")
    results = search_documentation("agents pydantic", limit=3)
    
    if results:
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  - Title: {result['metadata'].get('title', 'No title')}")
            print(f"  - URL: {result['metadata'].get('url', 'No URL')}")
            print(f"  - Distance: {result.get('distance', 'N/A')}")
    else:
        print("No results found")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())