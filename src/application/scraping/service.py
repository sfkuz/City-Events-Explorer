from __future__ import annotations
import asyncio
import logging

from infrastructure.scraping.registry import ScraperRegistry
from infrastructure.repositories.postgres_feed_repository import PostgresFeedRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository
from application.scraping.normalize import NormalizationService

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(
            self,
            feed_repo: PostgresFeedRepository,
            listings_repo: PostgresEventListingsRepository,
            registry: ScraperRegistry,
            normalization_service: NormalizationService,
            max_workers: int = 4
    ) -> None:
        self._feed_repo = feed_repo
        self._listings_repo = listings_repo
        self._registry = registry
        self._normalization_service = normalization_service
        self._semaphore = asyncio.Semaphore(max_workers)

    async def run_discovery_cycle(self) -> None:
        logger.info("Starting discovery cycle...")

        feeds = await self._feed_repo.get_active_feeds()
        if not feeds:
            logger.info("No active feeds found.")
            return

        tasks = [self._process_feed(feed) for feed in feeds]
        await asyncio.gather(*tasks)
        await self._normalization_service.run_normalization()

        logger.info("Discovery cycle completed.")

    async def _process_feed(self, feed) -> None:
        async with self._semaphore:
            logger.info(f"Processing feed: {feed.feed_url} (Source: {feed.source_code})")
            try:
                scraper = self._registry.get(feed.source_code)

                cards = await scraper.discover_events(feed.feed_url)

                if cards:
                    await self._listings_repo.upsert_discovered_events(feed.source_id, cards)

                await self._feed_repo.mark_feed_scraped(feed.feed_id)

                logger.info(f"Successfully processed feed {feed.feed_url}. Found {len(cards)} events.")
            except Exception as e:
                logger.error(f"Error processing feed {feed.feed_url}: {e}", exc_info=True)