import httpx
import logging
from application.scraping.ports import IFetcher
from application.scraping.retry import with_retry

logger = logging.getLogger(__name__)


class StaticFetcher(IFetcher):
    def __init__(self):
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
    @with_retry()
    async def fetch_html(self, url: str, headers: dict | None = None) -> str:
        req_headers = self.default_headers.copy()
        if headers:
            req_headers.update(headers)

        logger.info(f"Fetching URL: {url}")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=req_headers)
            response.raise_for_status()
            return response.text