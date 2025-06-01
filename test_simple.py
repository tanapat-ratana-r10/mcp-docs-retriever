#!/usr/bin/env python
import asyncio
from mcp_docs_retriever.server import add_documentation, search_documentation


async def test_simple():
    print("Simple test of MCP Documentation Server\n")
    
    # Test 1: Add a single page
    print("1. Adding Pydantic AI homepage...")
    result = await add_documentation(
        url="https://ai.pydantic.dev",
        scrape_subpages=False
    )
    print(f"Result: {result}\n")
    
    print("Done! The documentation has been added to the database.")
    print("The search functionality requires sentence transformers to be fully installed.")
    print("\nTo complete the installation, run: uv sync")


if __name__ == "__main__":
    asyncio.run(test_simple())