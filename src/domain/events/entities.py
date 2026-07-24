from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(slots=True, kw_only=True)
class Event:
    id: UUID = field(default_factory=uuid4)
    title: str
    location: str | None = None
    genre: str | None = None
    event_type: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    organizer_name: str
    url: str
    cover_image_url: str | None = None
    price: int | None = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.price is not None and self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.end_at and self.end_at <= self.start_at:
            raise ValueError("End date must be after start date")
        if not self.title or not str(self.title).strip():
            raise ValueError("Title cannot be empty")

    @property
    def is_free(self) -> bool:
        return self.price == 0 or self.price is None

    @property
    def is_finished(self) -> bool:
        return datetime.now(timezone.utc) > self.start_at