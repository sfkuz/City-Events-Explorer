from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import AsyncExitStack
from aiogram import Bot, Dispatcher

from app.bootstrap import bootstrap_application, Application
from infrastructure.config import load_settings
from infrastructure.logging import configure_logging
from application.events.service import EventService
from infrastructure.repositories.postgres_event_repository import PostgresEventRepository
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
            event_service = EventService(event_repo)

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