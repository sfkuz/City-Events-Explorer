from abc import ABC, abstractmethod
from application.scraping.dto import EventCard, EventDetails
from typing import Any

class IFetcher(ABC):
    @abstractmethod
    async def fetch_html(self, url: str, headers: dict | None = None) -> str:
        ...

    @abstractmethod
    async def post_json(self, url: str, json_payload: dict, headers: dict | None = None) -> dict[str, Any]:
        ...

class ISourceScraper(ABC):
    @abstractmethod
    async def discover_events(self, feed_url: str) -> list[EventCard]:
        ...

    @abstractmethod
    async def scrape_event_details(self, event_url: str) -> EventDetails:
        ...