import logging

from domain.events.entities import Event
from infrastructure.repositories.postgres_event_repository import PostgresEventRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository
from domain.events.enum import AVAILABLE_GENRES, AVAILABLE_TYPES

logger = logging.getLogger(__name__)

class NormalizationService:
    def __init__(self,
                 listings_repo: PostgresEventListingsRepository,
                 event_repo: PostgresEventRepository):
        self._listings_repo = listings_repo
        self._event_repo = event_repo

    async def run_normalization(self) -> None:
        logger.info('Starting normalization service')

        raw_events = await self._listings_repo.get_unprocessed_events()
        if not raw_events:
            logger.info('No unprocessed events found')
            return

        processed_urls = []
        valid_events_count = 0

        for card in raw_events:
            genre = str(card.genre).lower() if card.genre else ""
            event_type = str(card.event_type).lower() if card.event_type else ""

            if not genre or not event_type:
                processed_urls.append(card.source_event_url)
                continue

            is_valid_genre = genre in AVAILABLE_GENRES
            is_valid_type = event_type in AVAILABLE_TYPES

            if is_valid_genre or is_valid_type:
                domain_event = Event(
                    title=card.title,
                    location=card.location or card.city_text,
                    genre=genre,
                    event_type=event_type,
                    start_at=card.event_start_at,
                    end_at=card.event_end_at,
                    organizer_name="Trojmisto.pl" if not card.source_organizer_name else card.source_organizer_name,
                    url=card.source_event_url,
                    cover_image_url=card.cover_image_url,
                    price=card.price_min
                )

                try:
                    await self._event_repo.add(domain_event)
                    valid_events_count += 1
                    processed_urls.append(card.source_event_url)
                except Exception as e:
                    logger.error(f'Failed to save normalized event {card.source_event_url}: {e}')
            else:
                processed_urls.append(card.source_event_url)

        if processed_urls:
            await self._listings_repo.mark_as_normalized(processed_urls)

        logger.info(f'Normalization finished. Saved {valid_events_count} events')