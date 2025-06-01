#!/usr/bin/env python
import asyncio
from mcp_docs_retriever.server import mcp

if __name__ == "__main__":
    asyncio.run(mcp.run())