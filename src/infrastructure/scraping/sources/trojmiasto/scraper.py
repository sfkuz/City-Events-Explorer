import json
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin

from selectolax.parser import HTMLParser

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)


class TrojmiastoScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher

    async def discover_events(self, feed_url: str) -> list[EventCard]:
        html = await self._fetcher.fetch_html(feed_url)

        tree = HTMLParser(html)

        events_dict = self._extract_events_from_json(tree)
        logger.debug(f"Extracted {len(events_dict)} valid events from JSON-LD")

        self._enrich_events_from_html(tree, feed_url, events_dict)

        return list(events_dict.values())

    async def scrape_event_details(self, event_url: str) -> EventDetails:
        return EventDetails()

    def _extract_events_from_json(self, tree: HTMLParser) -> dict[str, EventCard]:
        events_dict = {}
        json_scripts = tree.css("script[type='application/ld+json']")

        for script in json_scripts:
            content = script.text(strip=True)
            if not content:
                continue

            try:
                data = json.loads(content)
                items = data if isinstance(data, list) else [data]

                for item in items:
                    if not isinstance(item, dict) or item.get("@type") != "Event":
                        continue

                    event_url = item.get("url")
                    if not event_url:
                        continue

                    norm_url = self._normalize_url(event_url)

                    price = item.get("offers", {}).get("price")

                    card = EventCard(
                        external_event_id=norm_url.strip('/').split('/')[-1],
                        source_event_url=event_url,
                        title=item.get("name", "Unknown").strip(),
                        event_start_at=self._safe_parse_dt(item.get("startDate")),
                        event_end_at=self._safe_parse_dt(item.get("endDate")),
                        city_text=item.get("location", {}).get("address", {}).get("addressLocality"),
                        location=item.get("location", {}).get("name"),
                        cover_image_url=item.get("image"),
                        price_min=int(float(price)) if price is not None else None,
                        source_organizer_name=item.get("performer", {}).get("name", "Unknown"),
                        metadata_json={"description": item.get("description")},
                        detail_complete=True
                    )
                    events_dict[norm_url] = card

            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON-LD block")
            except Exception as e:
                logger.error(f"Error parsing JSON event item: {e}")

        return events_dict

    def _enrich_events_from_html(self, tree: HTMLParser, feed_url: str, events_dict: dict[str, EventCard]) -> None:
        html_cards = tree.css(".event__item__container")

        for html_card in html_cards:
            link_el = html_card.css_first("a")
            if not link_el or not link_el.attributes.get("href"):
                continue

            raw_url = urljoin(feed_url, link_el.attributes["href"])
            norm_url = self._normalize_url(raw_url)

            if norm_url in events_dict:
                target_event = events_dict[norm_url]

                type_el = html_card.css_first(".event__item__category")
                if type_el:
                    target_event.event_type = type_el.text(strip=True).title()

                genre_el = html_card.css_first(".event__item__types")
                if genre_el:
                    target_event.genre = genre_el.text(strip=True).title()

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return clean_url.rstrip('/')

    @staticmethod
    def _safe_parse_dt(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            clean_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except ValueError:
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None