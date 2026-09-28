import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.parse

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)

GOING_CATEGORY_TO_TYPE = {
    'koncerty': 'koncerty',
    'rozrywka': 'imprezy rozrywkowe',
    'kultura': 'koncerty'
}

GOING_TAGS_TO_GENRE = {
    'jazz': 'jazz',
    'pop': 'pop',
    'rock': 'rock/punk',
    'punk': 'rock/punk',
    'muzyka klasyczna': 'muzyka poważna',
    'koncerty przy świecach': 'muzyka poważna',
    'muzyka filmowa': 'muzyka filmowa',
    'techno': 'muzyka elektroniczna',
    'house': 'muzyka elektroniczna',
    'elektronika': 'muzyka elektroniczna',
    'alternatywa': 'muzyka alternatywna',
    'rap': 'hip-hop',
    'festiwale muzyczne': 'festiwal muzyczny',
    'blues': 'blues/soul',
    'r&b soul': 'blues/soul'
}

class GoingScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher
        self.algolia_app_id = "FAFFKUSLK0"
        self.algolia_api_key = "2116b4baed0596249c1f98b9a20dfc6c"
        self.algolia_url = f"https://{self.algolia_app_id}-dsn.algolia.net/1/indexes/*/queries"

        self.headers = {
            "x-algolia-application-id": self.algolia_app_id,
            "x-algolia-api-key": self.algolia_api_key,
        }

    async def discover_events(self, feed_url: str) -> list[EventCard]:
        all_events = []
        page = 0
        total_pages = 1

        while page < total_pages:
            logger.info(f"Going.pl: Fetching Algolia page {page + 1}/{total_pages}")

            params = {
                "page": page,
                "hitsPerPage": 100,
                "facetFilters": "locations_names:Pomorskie",
            }
            encoded_params = urllib.parse.urlencode(params, safe='[]":')

            payload = {
                "requests": [
                    {
                        "indexName": "search-main",
                        "params": encoded_params
                    }
                ]
            }

            try:
                response = await self._fetcher.post_json(self.algolia_url, json_payload=payload, headers=self.headers)
                data = response.get("results", [])[0]

                hits = data.get("hits", [])
                total_pages = data.get("nbPages", 1)

                for hit in hits:
                    card = self._parse_hit_to_card(hit)
                    if card:
                        all_events.append(card)
                page += 1

            except Exception as e:
                logger.error(f"Error fetching Algolia for Going.pl: {e}", exc_info=True)
                break
        return all_events

    async def scrape_event_details(self, event_url: str) -> EventDetails:
        return EventDetails()

    def _parse_hit_to_card(self, hit: dict) -> EventCard | None:

        external_id = str(hit.get("objectID"))

        slug = hit.get("slug")
        if not slug:
            return None
        event_url = f"https://goingapp.pl/wydarzenie/{slug}"

        raw_start_date = hit.get("start_date")
        start_at = None
        if raw_start_date:
            try:
                clean_date = raw_start_date.replace("Z", "+00:00")
                dt_utc = datetime.fromisoformat(clean_date)
                start_at = dt_utc.astimezone(ZoneInfo("Europe/Warsaw"))
            except ValueError:
                pass

        if not start_at:
            return None

        raw_category = str(hit.get("category_name",  "")).lower()
        event_type = GOING_CATEGORY_TO_TYPE.get(raw_category, None)

        event_genre = None
        raw_tags = hit.get("tags_names", [])
        for tag in raw_tags:
            tag_lower = str(tag).lower()
            if tag_lower in GOING_TAGS_TO_GENRE:
                event_genre = GOING_TAGS_TO_GENRE[tag_lower]
                break

        title = hit.get("name_pl") or "Unknown"

        price_min = hit.get("price")
        if price_min is not None:
            price_min = int(price_min)

        raw_thumb = hit.get("thumbnail")
        cover_image = None
        if raw_thumb:
            if raw_thumb.startswith("http"):
                cover_image = raw_thumb
            else:
                cover_image = f"https://cdn.goingapp.pl/{raw_thumb}"

        locations = hit.get("locations_names")
        city_text = None
        if isinstance(locations, list) and len(locations) > 0:
            city_text = str(locations[0])
        elif isinstance(locations, str):
            city_text = locations

        place = hit.get("place_name")
        location_text = None
        if isinstance(place, list) and len(place) > 0:
            location_text = ", ".join([str(p) for p in place])
        elif isinstance(place, str):
            location_text = place

        return EventCard(
            external_event_id=external_id,
            source_event_url=event_url,
            title=title,
            event_start_at=start_at,
            city_text=city_text,
            location=location_text,
            genre=event_genre,
            event_type=event_type,
            cover_image_url=cover_image,
            price_min=price_min,
            source_organizer_name="Going.",
            detail_complete=True
        )