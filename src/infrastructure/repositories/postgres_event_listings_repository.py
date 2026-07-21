from __future__ import annotations
import logging
import json
from typing import Sequence
import asyncpg

from application.scraping.dto import EventCard
from application.scraping.dto import EventCard

logger = logging.getLogger(__name__)


class PostgresEventListingsRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def upsert_discovered_events(self, source_id: str, cards: Sequence[EventCard]) -> None:
        if not cards:
            return

        query = """
                INSERT INTO event_listings (source_id, external_event_id, source_event_url, title,
                                            event_start_at, event_end_at, city_text, location, genre, event_type,
                                            cover_image_url, price, price_currency, metadata_json,
                                            detail_status, first_seen_at, last_seen_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::jsonb, $15, NOW(),
                        NOW()) ON CONFLICT (source_id, source_event_url) DO
                UPDATE SET
                    title = EXCLUDED.title,
                    event_start_at = COALESCE (EXCLUDED.event_start_at, event_listings.event_start_at),
                    event_end_at = EXCLUDED.event_end_at,
                    city_text = EXCLUDED.city_text,
                    location = EXCLUDED.location,
                    genre = EXCLUDED.genre,
                    event_type = EXCLUDED.event_type,
                    cover_image_url = EXCLUDED.cover_image_url,
                    price = EXCLUDED.price,
                    metadata_json = EXCLUDED.metadata_json,
                    "status" = 'active',
                    last_seen_at = NOW()
                """

        values = []
        for card in cards:
            detail_status = 'done' if card.detail_complete else 'pending'
            meta_json = json.dumps(card.metadata_json) if card.metadata_json else '{}'

            values.append((
                source_id, card.external_event_id, card.source_event_url, card.title,
                card.event_start_at, card.event_end_at, card.city_text, card.location,
                card.genre, card.event_type, card.cover_image_url, card.price_min,
                card.price_currency, meta_json, detail_status
            ))

        try:
            await self._pool.executemany(query, values)
            logger.info(f"Upserted {len(cards)} events for source {source_id}")
        except Exception as e:
            logger.error(f"Failed to upsert events: {e}")
            raise

    async def get_unprocessed_events(self, source_id: str) -> list[EventCard]:
        query = """
        SELECT * FROM  event_listings 
        WHERE detail_status = 'done'
        AND status != 'normalized'
        """
        rows = await self._pool.fetch(query)
        cards = []
        for row in rows:
            cards.append(EventCard(
                external_event_id=row['external_event_id'],
                source_event_url=row['source_event_url'],
                title=row['title'],
                event_start_at=row['event_start_at'],
                event_end_at=row['event_end_at'],
                city_text=row['city_text'],
                location=row['location'],
                genre=row['genre'],
                event_type=row['event_type'],
                cover_image_url=row['cover_image_url'],
                price_min=row['price'],
                price_currency=row['price_currency']
            ))
        return cards

    async def mark_as_normalized(self, urls: list[str]) -> None:
        if not urls:
            return
        query = "UPDATE event_listings SET status = 'normalized' WHERE source_event_url = ANY($1::text[])"
        await self._pool.execute(query, urls)