from __future__ import annotations
from application.scraping.ports import ISourceScraper

class ScraperRegistry:
    def __init__(self) -> None:
        self._scrapers: dict[str, ISourceScraper] = {}

    def register(self, source_code: str, scraper: ISourceScraper) -> None:
        self._scrapers[source_code] = scraper

    def get(self, source_code: str) -> ISourceScraper:
        if source_code not in self._scrapers:
            raise ValueError(f"Scraper for source '{source_code}' not found in registry")
        return self._scrapers[source_code]