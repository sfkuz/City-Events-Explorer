import httpx
import logging
from fake_useragent import UserAgent
from application.scraping.ports import IFetcher
from application.scraping.retry import with_retry

logger = logging.getLogger(__name__)


class StaticFetcher(IFetcher):
    def __init__(self):
        self.ua = UserAgent(os='windows', browsers=['chrome', 'firefox', 'opera', 'safari'])

    @with_retry()
    async def fetch_html(self, url: str, headers: dict | None = None) -> str:
        req_headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        if headers:
            req_headers.update(headers)

        logger.info(f"Fetching URL: {url} | UA: {req_headers['User-Agent']}")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=req_headers)
            response.raise_for_status()
            return response.text