from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from encodings.iso8859_4 import decoding_table

from fastapi_cloud_cli.utils.api import attempts

from infrastructure.scraping.registry import ScraperRegistry
from infrastructure.repositories.postgres_feed_repository import PostgresFeedRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository
from application.scraping.normalize import NormalizationService
from application.scraping.dto import PendingDetailEvent

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

    async def _process_single_detail(self, pending_event: PendingDetailEvent) -> None:
        async with self._semaphore:
            logger.info(f"Fetching details for {pending_event.source_event_url}")
            try:
                scraper = self._registry.get(pending_event.source_code)
                details = await scraper.scrape_event_details(pending_event.source_event_url)
                await self._listings_repo.mark_detail_success(pending_event.listing_id ,details)
            except Exception as e:
                attempts = pending_event.detail_attempts + 1
                delay_minutes = 15 * (attempts ** 5)
                next_retry = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

                detail_status = 'dead' if attempts >= 5 else 'failed'

                await self._listings_repo.mark_detail_failed(
                    listing_id=pending_event.listing_id,
                    error_msg=str(e),
                    attempts=attempts,
                    next_retry=next_retry,
                    status=detail_status
                )


    async def run_details_cycle(self) -> None:
        logger.info("Starting detail discovery cycle...")
        pending_events = await self._listings_repo.get_events_for_details(limit=20)

        if not pending_events:
            logger.info("No pending events found.")
            return

        tasks = [self._process_single_detail(event) for event in pending_events]
        await asyncio.gather(*tasks)

        logger.info("Detail discovery cycle completed.")