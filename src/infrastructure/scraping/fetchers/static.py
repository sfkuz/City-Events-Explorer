import httpx
import logging
import random
from application.scraping.ports import IFetcher
from application.scraping.retry import with_retry

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
]


class StaticFetcher(IFetcher):
    def __init__(self):
        pass

    @with_retry()
    async def fetch_html(self, url: str, headers: dict | None = None) -> str:
        req_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        if headers:
            req_headers.update(headers)

        logger.info(f"Fetching URL: {url}")
        logger.debug(f"Request headers for {url}: {req_headers}")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=req_headers)
            response.raise_for_status()
            return response.text