from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import Iterable, Sequence
from uuid import UUID

from domain.events.entities import Event

class IEventRepository(ABC):

    @abstractmethod
    async def add(self, event: Event) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> Event | None:
        ...

    @abstractmethod
    async def get_all(self) -> Iterable[Event]:
        ...

    @abstractmethod
    async def delete(self, event_id: UUID) -> None:
        ...

    @abstractmethod
    async def get_by_event_type(self, event_type: str) -> Sequence[Event]:
        ...

    @abstractmethod
    async def get_by_event_genre(self, genre: str) -> Sequence[Event]:
        ...

    @abstractmethod
    async def get_by_start_at(self, start_at: datetime) -> Sequence[Event]:
        ...