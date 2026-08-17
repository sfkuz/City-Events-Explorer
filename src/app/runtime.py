from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack

from infrastructure.config import Settings
from app.bootstrap import bootstrap_application

logger = logging.getLogger(__name__)

async def run(settings: Settings) -> None:
    logger.info("Application starting")

    try:
        async with AsyncExitStack() as stack:
            application = await bootstrap_application(settings, stack)

            application.cron_service.setup_jobs()
            application.cron_service.start()
            stack.callback(application.cron_service.stop)

            logger.info("Application started")

            await application.dp.start_polling(
                application.bot,
                close_bot_session=False,
            )

    except asyncio.CancelledError:
        logger.info("Application cancelled")
        raise
    finally:
        logger.info("Application stopped")