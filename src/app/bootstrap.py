from __future__ import annotations

import logging
import asyncpg
from contextlib import AsyncExitStack
from dataclasses import dataclass

from infrastructure.config import Settings, load_settings
from infrastructure.db.pool import create_db_pool, close_db_pool

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class Application:
    settings: Settings
    db_pool: asyncpg.Pool


async def bootstrap_application(stack: AsyncExitStack) -> Application:
    settings = load_settings()
    logger.info("Settings loaded successfully")
    db_pool = await create_db_pool(settings)
    stack.push_async_callback(close_db_pool, db_pool)
    logger.info("Database pool initialized")

    return Application(
        settings=settings,
        db_pool=db_pool,
    )