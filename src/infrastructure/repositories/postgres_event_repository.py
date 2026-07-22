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
            id, title, location, genre, event_type,
            start_at, end_at, organizer_name, url,
            cover_image_url, price, created_at, updated_at) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8,$9, $10, $11, $12, $13)
                ON CONFLICT (url) DO UPDATE SET 
                title = EXCLUDED.title,
                location = EXCLUDED.location,
                start_at = EXCLUDED.start_at,
                end_at = EXCLUDED.end_at,
                price = EXCLUDED.price,
                cover_image_url = EXCLUDED.cover_image_url,
                updated_at = NOW()
        """
        await self._pool.execute(
            query,
            event.id, event.title, event.location,
            event.genre, event.event_type, event.start_at, event.end_at,
            event.organizer_name, event.url, event.cover_image_url,
            event.price, event.created_at, event.updated_at
        )

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

    async def get_by_start_at(self, start_at: datetime.date) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE DATE (start_at) = $1 ORDER BY start_at ASC"
        rows = await self._pool.fetch(query, start_at)
        return [self._map_to_domain(row) for row in rows]

    async def get_by_event_genre(self, genre: str) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE genre = $1 ORDER BY start_at ASC"
        rows = await self._pool.fetch(query, genre)
        return [self._map_to_domain(row) for row in rows]

    async def delete(self, event_id: UUID) -> None:
        query = "DELETE FROM events WHERE id = $1"
        await self._pool.execute(query, event_id)

    async def search_events(
            self,
            genres: list[str] = None,
            types: list[str] = None,
            date_from: datetime = None,
            date_to: datetime = None,
            limit: int = 1,
            offset: int = 0
    ) -> Sequence[Event]:
        query = "SELECT * FROM events WHERE 1=1"
        args = []
        arg_idx = 1

        if genres:
            query += f'AND genre = ANY(${arg_idx}::text[])'
            args.append(genres)
            arg_idx += 1

        if types:
            query += f'AND event_type = ANY(${arg_idx}::text[])'
            args.append(types)
            arg_idx += 1

        if date_from:
            query += f'AND start_at >= ${arg_idx}'
            args.append(date_from)
            arg_idx += 1

        if date_to:
            query += f'AND start_at <= ${arg_idx}'
            args.append(date_to)
            arg_idx += 1

        query += f"ORDER BY start_at ASC LIMIT ${arg_idx} OFFSET {arg_idx+1 }"
        args.extend([limit, offset])
        rows = await self._pool.fetch(query, *args)
        return [self._map_to_domain(row) for row in rows]

    async def count_search_events(
            self,
            genres: list[str] | None = None,
            types: list[str] | None = None,
            date_from: datetime | None = None,
            date_to: datetime | None = None
    ) -> int:
        query = "SELECT count(*) FROM events WHERE 1=1"
        args = []
        arg_idx = 1

        if genres:
            query += f'AND genre = ANY(${arg_idx}::text[])'
            args.append(genres)
            arg_idx += 1

        if types:
            query += f'AND event_type = ANY(${arg_idx}::text[])'
            args.append(types)
            arg_idx += 1

        if date_from:
            query += f'AND start_at >= ${arg_idx}'
            args.append(date_from)
            arg_idx += 1

        if date_to:
            query += f'AND start_at <= ${arg_idx}'
            args.append(date_to)
            arg_idx += 1

        count = await self._pool.fetchval(query, *args)
        return count