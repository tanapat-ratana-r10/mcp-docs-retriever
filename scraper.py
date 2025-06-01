import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, Dict, List, Optional
from tqdm import tqdm
import re

class DocumentationScraper:
    def __init__(self, base_url: str, allowed_domains: Optional[List[str]] = None):
        self.base_url = base_url
        self.allowed_domains = allowed_domains or [urlparse(base_url).netloc]
        self.visited_urls: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            parsed.netloc in self.allowed_domains
            and not url.endswith(('.pdf', '.zip', '.tar.gz', '.png', '.jpg', '.jpeg', '.gif'))
            and not any(ext in url.lower() for ext in ['/api/', '/cdn/', '/static/', '/assets/'])
        )

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            if self._is_valid_url(full_url):
                links.add(full_url)
        return links

    def _extract_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive newlines

        # Get title
        title = soup.title.string if soup.title else ""

        return {
            "title": title,
            "content": text
        }

    async def scrape_page(self, url: str) -> Optional[Dict]:
        if url in self.visited_urls:
            return None

        self.visited_urls.add(url)
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                content = self._extract_content(soup)
                
                return {
                    "url": url,
                    "title": content["title"],
                    "content": content["content"],
                    "metadata": {
                        "source_url": url,
                        "scraped_at": str(asyncio.get_event_loop().time())
                    }
                }
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    async def scrape_all(self, max_pages: int = 100) -> List[Dict]:
        to_visit = {self.base_url}
        results = []
        
        with tqdm(total=max_pages, desc="Scraping pages") as pbar:
            while to_visit and len(results) < max_pages:
                current_url = to_visit.pop()
                if current_url in self.visited_urls:
                    continue

                page_data = await self.scrape_page(current_url)
                if page_data:
                    results.append(page_data)
                    pbar.update(1)

                    # Extract new links
                    async with self.session.get(current_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            new_links = self._extract_links(soup, current_url)
                            to_visit.update(new_links - self.visited_urls)

        return results 