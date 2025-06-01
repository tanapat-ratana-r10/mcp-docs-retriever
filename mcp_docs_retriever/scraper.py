import asyncio
from typing import Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md


async def scrape_url(url: str, client: httpx.AsyncClient) -> Tuple[str, str]:
    """Scrape a single URL and return title and markdown content."""
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get title
        title = soup.find('title')
        title_text = title.string if title else urlparse(url).path
        
        # Convert to markdown
        content = md(str(soup.body) if soup.body else str(soup))
        
        return title_text, content
    except Exception as e:
        return f"Error scraping {url}", f"Failed to scrape: {str(e)}"


async def discover_urls(base_url: str, client: httpx.AsyncClient, max_depth: int = 2) -> Set[str]:
    """Discover all URLs under a domain with depth limit."""
    visited = set()
    to_visit = {base_url}
    domain = urlparse(base_url).netloc
    
    for depth in range(max_depth):
        if not to_visit:
            break
            
        current_level = list(to_visit)
        to_visit = set()
        
        for url in current_level:
            if url in visited:
                continue
                
            visited.add(url)
            
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)
                    
                    # Only follow links on the same domain
                    if parsed.netloc == domain and full_url not in visited:
                        to_visit.add(full_url)
                        
            except Exception:
                continue
    
    return visited


async def scrape_documentation_site(url: str, max_depth: int = 2, max_pages: int = 50) -> list[dict]:
    """Scrape an entire documentation site and return list of pages."""
    pages = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Discover URLs
        urls = await discover_urls(url, client, max_depth)
        urls = list(urls)[:max_pages]  # Limit number of pages
        
        # Scrape each URL
        for page_url in urls:
            title, content = await scrape_url(page_url, client)
            
            if not content.startswith("Failed to scrape:"):
                pages.append({
                    "title": title,
                    "content": content,
                    "url": page_url,
                    "domain": urlparse(page_url).netloc
                })
                
            # Small delay to be respectful
            await asyncio.sleep(0.5)
    
    return pages