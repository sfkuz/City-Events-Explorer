from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass

from aiogram import Bot, Dispatcher

from infrastructure.config import Settings
from infrastructure.db.pool import create_db_pool, close_db_pool

from infrastructure.repositories.postgres_feed_repository import PostgresFeedRepository
from infrastructure.repositories.postgres_event_repository import PostgresEventRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository

from infrastructure.scraping.sources.trojmiasto.scraper import TrojmiastoScraper
from infrastructure.scraping.fetchers.static import StaticFetcher
from infrastructure.scraping.registry import ScraperRegistry

from application.events.service import EventService
from application.scraping.service import ScraperService
from application.scraping.normalize import NormalizationService
from application.cron_service import CronService

from app.tg_bot.handlers.router import main_router

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class Application:
    settings: Settings
    bot: Bot
    dp: Dispatcher
    cron_service: CronService


async def bootstrap_application(settings: Settings,stack: AsyncExitStack) -> Application:
    logger.info("Bootstrapping application dependencies...")

    db_pool = await create_db_pool(settings)
    stack.push_async_callback(close_db_pool, db_pool)

    event_repo = PostgresEventRepository(db_pool)
    feed_repo = PostgresFeedRepository(db_pool)
    listings_repo = PostgresEventListingsRepository(db_pool)

    fetcher = StaticFetcher()
    trojmiasto_scraper = TrojmiastoScraper(fetcher)

    registry = ScraperRegistry()
    registry.register("trojmiasto", trojmiasto_scraper)

    event_service = EventService(event_repo)
    normalization_service = NormalizationService(listings_repo, event_repo)

    scraper_service = ScraperService(
        feed_repo = feed_repo,
        listings_repo = listings_repo,
        registry = registry,
        normalization_service = normalization_service
    )

    cron_service = CronService(scraper_service, settings)
    stack.callback(cron_service.stop)

    bot = Bot(token=settings.tg_bot_token)
    stack.push_async_callback(bot.session.close)

    dp = Dispatcher()
    dp["event_service"] = event_service
    dp.include_router(main_router)

    return Application(
        settings=settings,
        bot=bot,
        dp=dp,
        cron_service=cron_service,
    )