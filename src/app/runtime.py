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

async def run_bot(app: Application) -> None:
    bot = Bot(token=app.settings.tg_bot_token)
    dp = Dispatcher()

    event_repo = PostgresEventRepository(app.db_pool)
    event_service = EventService(event_repo)

    dp['event_service'] = event_service
    dp.include_router(main_router)

    logger.info('Starting bot...')
    await dp.start_polling(bot)

async def _wait_for_shutdown_signal() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_signal(sig: signal.Signals) -> None:
        logger.info("Shutdown signal received: %s", sig.name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop_event.set())

    await stop_event.wait()


async def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    logger.info("Application starting...")

    try:
        async with AsyncExitStack() as stack:
            app = await bootstrap_application(stack)

            logger.info("Application started successfully")
            bot_task = asyncio.create_task(run_bot(app))
            logger.info("Waiting for shutdown signal...")

            await _wait_for_shutdown_signal()

            logger.info("Application stopping...")
            bot_task.cancel()

    except asyncio.CancelledError:
        logger.warning("Application task cancelled")
        raise
    except Exception:
        logger.exception("Fatal error during application lifecycle")
        raise
    finally:
        logger.info("Application stopped")