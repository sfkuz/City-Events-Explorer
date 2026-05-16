from __future__ import annotations
import asyncpg
from dataclasses import dataclass


@dataclass
class FeedToScrape:
    feed_id: str
    source_id: str
    source_code: str
    feed_url: str


class PostgresFeedRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_active_feeds(self) -> list[FeedToScrape]:
        query = """
                SELECT f.id as feed_id, s.id as source_id, s.code as source_code, f.feed_url
                FROM source_category_feeds f
                         JOIN sources s ON f.source_id = s.id
                WHERE f.is_active = true \
                  AND s.is_active = true \
                """
        rows = await self._pool.fetch(query)
        return [FeedToScrape(**row) for row in rows]

    async def mark_feed_scraped(self, feed_id: str) -> None:
        query = "UPDATE source_category_feeds SET last_scraped_at = NOW() WHERE id = $1"
        await self._pool.execute(query, feed_id)