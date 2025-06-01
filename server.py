"""server.py – MCP Docs Server with semantic search (FastMCP ≥ 2.2)
================================================================
Exposes two tools:
  • add_documentation
  • search_documentation

Choose Qdrant backend via env vars:
  QDRANT_MODE=memory|local|remote (default remote)

Run (stdio):
    QDRANT_MODE=memory python server.py
Or SSE:
    python server.py --transport sse --port 8080
"""

from __future__ import annotations

import logging
import queue
import re
import sys
from html import unescape
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Comment
from fastmcp import FastMCP
from html2text import HTML2Text
from pydantic import BaseModel, Field, root_validator, validator

from storage import add_documentation as _add_doc
from storage import search_documentation as _search_doc

###############################################################################
# Logging
###############################################################################

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(msg)s")
log = logging.getLogger(__name__)

###############################################################################
# Pydantic input schemas
###############################################################################

class AddDocumentationArgs(BaseModel):
    """Args for add_documentation (direct text OR crawler)."""

    # Direct-text mode
    title: Optional[str] = Field(None, description="Document title")
    content: Optional[str] = Field(None, description="Markdown / HTML text body")

    # Crawler mode
    entrypoint_url: Optional[str] = Field(
        None,
        description="Root page to crawl, e.g. https://docs.example.com/",
    )
    prefix: Optional[str] = Field(
        None,
        description="Link prefix limiting the crawl (defaults to entrypoint path)",
    )

    # Common
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Extra metadata merged into every chunk payload"
    )

    @root_validator(skip_on_failure=True)
    def choose_mode(cls, values):  # noqa: D401,N805
        entry = values.get("entrypoint_url")
        title, content = values.get("title"), values.get("content")
        if entry is None:
            if not (title and content):
                raise ValueError("Provide (title & content) or entrypoint_url")
        else:
            if title or content:
                raise ValueError("Do not mix entrypoint_url with title/content")
        return values

    @validator("entrypoint_url")
    def url_must_be_http(cls, v):  # noqa: D401,N805
        if v and not re.match(r"https?://", v):
            raise ValueError("entrypoint_url must start with http:// or https://")
        return v


class SearchDocumentationArgs(BaseModel):
    query: str = Field(..., description="Natural‑language query")
    top_k: int = Field(5, ge=1, le=50, description="Number of hits")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Exact‑match metadata filters"
    )

###############################################################################
# FastMCP bootstrap
###############################################################################

mcp = FastMCP(
    name="MCP‑Docs‑Storage",
    instructions="Semantic documentation storage and retrieval.",
)

###############################################################################
# Crawl helpers
###############################################################################

_h2md = HTML2Text()
_h2md.ignore_links = False
_h2md.protect_links = True
_h2md.ignore_images = True
_h2md.body_width = 0

_MAX_PAGES = 2000
_TIMEOUT = 10
_HEADERS = {"User-Agent": "MCP-Docs-Crawler/1.0"}


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    return str(soup)


def _to_md(html: str) -> str:
    return _h2md.handle(unescape(html))


def _crawl(entry: str, prefix: str) -> Dict[str, str]:
    pages: Dict[str, str] = {}
    seen: Set[str] = set([entry])
    q: queue.Queue[str] = queue.Queue()
    q.put(entry)
    while not q.empty() and len(pages) < _MAX_PAGES:
        url = q.get()
        try:
            r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.warning("Fetch failed %s: %s", url, e)
            continue
        pages[url] = _to_md(_clean_html(r.text))
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"].split("#", 1)[0]
            next_url = urljoin(url, href)
            if next_url.startswith(prefix) and next_url not in seen:
                seen.add(next_url)
                q.put(next_url)
    return pages

###############################################################################
# Tool: add_documentation
###############################################################################

@mcp.tool("add_documentation")

def add_documentation_tool(args: AddDocumentationArgs) -> Dict[str, Any]:
    """Ingest raw text or crawl a docs site and store embeddings."""
    if args.entrypoint_url:
        prefix = args.prefix or args.entrypoint_url.rstrip("/")
        pages = _crawl(args.entrypoint_url, prefix)
        point_ids: List[str] = []
        chunks = 0
        for url, md in pages.items():
            title = urlparse(url).path.rsplit("/", 1)[-1] or "index"
            ids = _add_doc(title=title, content=md, metadata={"url": url, **(args.metadata or {})})
            point_ids.extend(ids)
            chunks += len(ids)
        return {"status": "ok", "pages_crawled": len(pages), "chunks_added": chunks}

    # direct‑text mode
    ids = _add_doc(title=args.title, content=args.content, metadata=args.metadata)  # type: ignore[arg-type]
    return {"status": "ok", "chunks_added": len(ids)}

###############################################################################
# Tool: search_documentation
###############################################################################

@mcp.tool("search_documentation")

def search_documentation_tool(args: SearchDocumentationArgs) -> Dict[str, Any]:
    return {"results": _search_doc(args.query, top_k=args.top_k, filters=args.filters)}

###############################################################################
# Main entrypoint
###############################################################################

if __name__ == "__main__":
    mcp.run()
