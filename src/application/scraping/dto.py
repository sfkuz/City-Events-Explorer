from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, kw_only=True)
class EventDetails:
    description_text: str | None = None
    description_html: str | None = None
    price: int | None = None
    raw_html: str | None = None


@dataclass(slots=True, kw_only=True)
class EventCard:
    external_event_id: str
    source_event_url: str
    title: str
    event_start_at: datetime
    event_end_at: datetime | None = None
    city_text: str | None = None
    location: str | None = None
    genre: str | None = None
    event_type: str | None = None
    cover_image_url: str | None = None 
    price_min: int | None = None
    price_currency: str = "PLN"
    source_organizer_name: str | None = None
    source_organizer_url: str | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)

    detail_complete: bool = False