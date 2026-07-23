from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from aiogram import Bot, Dispatcher

from app.bootstrap import bootstrap_application
from infrastructure.config import load_settings
from infrastructure.logging import configure_logging

from application.events.service import EventService
from application.scraping.normalize import NormalizationService
from application.scraping.service import ScraperService
from application.cron_service import CronService

from infrastructure.repositories.postgres_event_repository import PostgresEventRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository
from infrastructure.repositories.postgres_feed_repository import PostgresFeedRepository

from infrastructure.scraping.fetchers.static import StaticFetcher
from infrastructure.scraping.sources.trojmiasto.scraper import TrojmiastoScraper
from infrastructure.scraping.registry import ScraperRegistry

from app.tg_bot.handlers.router import main_router

logger = logging.getLogger(__name__)

async def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    logger.info("Application starting...")

    try:
        async with AsyncExitStack() as stack:
            app = await bootstrap_application(stack)
            logger.info("Application started successfully")

            bot = Bot(token=app.settings.tg_bot_token)
            dp = Dispatcher()

            event_repo = PostgresEventRepository(app.db_pool)
            feed_repo = PostgresFeedRepository(app.db_pool)
            listings_repo = PostgresEventListingsRepository(app.db_pool)

            fetcher = StaticFetcher()
            trojmiasto_scraper = TrojmiastoScraper(fetcher)
            registry = ScraperRegistry()
            registry.register("trojmiasto", trojmiasto_scraper)

            event_service = EventService(event_repo)
            normalization_service = NormalizationService(listings_repo, event_repo)
            scraper_service = ScraperService(
                feed_repo=feed_repo,
                listings_repo=listings_repo,
                registry=registry,
                normalization_service=normalization_service
            )

            cron_service = CronService(scraper_service)
            cron_service.setup_jobs()
            cron_service.start()
            logger.info('Cron scheduler started')

            dp['event_service'] = event_service
            dp.include_router(main_router)

            logger.info("Starting bot pooling...")
            await dp.start_polling(bot)

    except asyncio.CancelledError:
        logger.warning("Application task cancelled")
        raise
    except Exception:
        logger.exception("Fatal error during application lifecycle")
        raise
    finally:
        logger.info("Application stopped")