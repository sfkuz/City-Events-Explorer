from __future__ import annotations
from uuid import UUID
from typing import Sequence
from datetime import datetime, timezone, timedelta

from domain.events.entities import Event
from domain.events.repository import IEventRepository

class EventService:
    def __init__(self, event_repository: IEventRepository):
        self._event_repository = event_repository

    async def add_event(self, event: Event) -> UUID | None:
        if event.is_finished:
            return None
        await self._event_repository.add(event)
        return event.id

    async def get_all_events(self, limit: int = 100) -> Sequence[Event] | None:
        return await self._event_repository.get_all(limit=limit)

    async def get_events_by_type(self, event_type: str) -> Sequence[Event]:
        return await self._event_repository.get_by_event_type(event_type)

    async def get_event_details(self, event_id: UUID) -> Event:
        event = await self._event_repository.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        return event

    async def get_events_for_today(self) -> Sequence[Event]:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        return await self._event_repository.get_by_start_at(today)

    async def search_events(
            self,
            genres: list[str] | None = None,
            types: list[str] | None = None,
            date_from: datetime | None = None,
            date_to: datetime | None = None,
            limit: int = 1,
            offset: int = 0
            ) -> Sequence[Event]:
        return await self._event_repository.search_events(
            genres=genres, types=types, date_from=date_from, date_to=date_to, limit=limit, offset=offset
        )


    async def count_search_events(
            self,
            genres: list[str] | None = None,
            types: list[str] | None = None,
            date_from: datetime | None = None,
            date_to: datetime | None = None
            ) -> int:
        return await self._event_repository.count_search_events(
            genres=genres, types=types, date_from=date_from, date_to=date_to
        )