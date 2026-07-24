from __future__ import annotations

import logging

import asyncpg
from asyncpg import Pool

from infrastructure.config import Settings

logger = logging.getLogger(__name__)


async def create_db_pool(settings: Settings) -> Pool:
    logger.info(
        "Creating PostgreSQL pool (min_size=%s, max_size=%s)",
        settings.db_pool_min_size,
        settings.db_pool_max_size,
    )

    pool = await asyncpg.create_pool(
        dsn=str(settings.database_url),
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        command_timeout=settings.db_connect_timeout_seconds,
    )
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")

    logger.info("PostgreSQL pool created and health check passed")
    return pool


async def close_db_pool(pool: Pool) -> None:
    logger.info("Closing PostgreSQL pool...")
    await pool.close()
    logger.info("PostgreSQL pool closed")