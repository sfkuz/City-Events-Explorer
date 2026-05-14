from __future__ import annotations
from typing import Sequence
from uuid import UUID
from datetime import datetime

import asyncpg
from domain.events.entities import Event
from domain.events.repository import IEventRepository

class PostgresEventRepository(IEventRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    def _map_to_domain(self, row: asyncpg.Record) -> Event:
        return Event(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            location=row["location"],
            genre=row["genre"],
            event_type=row["event_type"],
            start_at=row["start_at"],
            end_at=row["end_at"],
            organizer_name=row["organizer_name"],
            url=row["url"],
            cover_image_url=row["cover_image_url"],
            price=row["price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    async def add(self, event: Event) -> None:
        query = """
            INSERT INTO events (
            id, title, description, location, genre, event_type,
            start_at, end_at, organizer_name, url,
            cover_image_url, price, created_at, updated_at) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8,$9, $10, $11, $12, $13, $14)
        """
        try:
            await self._pool.execute(
                query,
                event.id, event.title, event.description, event.location,
                event.genre, event.event_type, event.start_at, event.end_at,
                event.organizer_name, event.url, event.cover_image_url,
                event.price, event.created_at, event.updated_at
            )
        except asyncpg.UniqueViolationError:
            raise

    async def get_by_id(self, event_id: UUID) -> Event:
        query = "SELECT * FROM events WHERE id = $1"
        row = await self._pool.fetchrow(query, event_id)

        if not row:
            return None
        return self._map_to_domain(row)

    async def get_all(self, limit: int = 100) -> Sequence[Event]:
        query = "SELECT * FROM events ORDER BY start_at DESC"
        rows = await self._pool.fetch(query, limit)
        return [self._map_to_domain(row) for row in rows]

    async def get_by_event_type(self, event_type: str) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE event_type = $1 ORDER BY start_at DESC"
        rows = await self._pool.fetch(query, event_type)
        return [self._map_to_domain(row) for row in rows]

    async def get_events_for_date(self, start_at: datetime.date) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE DATE (start_at) = $1 ORDER BY start_at ASC"
        rows = await self.pool.fetch(query, start_at)
        return [self._map_to_domain(row) for row in rows]

    async def get_by_genre(self, genre: str) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE genre = $1 ORDER BY start_at ASC"
        rows = await self.pool.fetch(query, genre)
        return [self._map_to_domain(row) for row in rows]

    async def delete(self, event_id: UUID) -> None:
        query = "DELETE FROM events WHERE id = $1"
        await self._pool.execute(query, event_id)