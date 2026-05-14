import json
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)


class TrojmiastoScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher

    async def discover_events(self, feed_url: str) -> list[EventCard]:
        html = await self._fetcher.fetch_html(feed_url)
        soup = BeautifulSoup(html, 'lxml')

        events_dict = {}

        json_scripts = soup.find_all("script", type="application/ld+json")
        logger.debug(f"Found JSON blocks: {len(json_scripts)}")

        for script in json_scripts:
            try:
                content = script.text.strip()
                if not content:
                    continue

                data = json.loads(content)
                items = data if isinstance(data, list) else [data]

                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "Event":
                        event_url = item.get("url")
                        if not event_url:
                            continue

                        ext_id = event_url.strip('/').split('/')[-1]

                        start_dt = datetime.fromisoformat(item.get("startDate"))
                        end_dt_str = item.get("endDate")
                        end_dt = datetime.fromisoformat(end_dt_str) if end_dt_str else None

                        price = None
                        if item.get("offers", {}).get("price") is not None:
                            price = int(float(item["offers"]["price"]))

                        card = EventCard(
                            external_event_id=ext_id,
                            source_event_url=event_url,
                            title=item.get("name", "Unknown").strip(),
                            event_start_at=start_dt,
                            event_end_at=end_dt,
                            city_text=item.get("location", {}).get("address", {}).get("addressLocality"),
                            location=item.get("location", {}).get("name"),
                            cover_image_url=item.get("image"),
                            price_min=price,
                            source_organizer_name=item.get("performer", {}).get("name", "Unknown"),
                            metadata_json={
                                "description": item.get("description")
                            },
                            detail_complete=True
                        )
                        events_dict[event_url] = card

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error parsing JSON event: {e}")

        html_cards = soup.select(".event__item__container")
        logger.debug(f"In HTML found cards: {len(html_cards)}")

        domain = f"https://{urlparse(feed_url).netloc}"

        for html_card in html_cards:
            link_el = html_card.select_one("a")
            if not link_el:
                continue

            card_url = link_el.get("href")
            # Если ссылка начинается с '/', добавляем домен
            if card_url and card_url.startswith('/'):
                card_url = f"{domain}{card_url}"

            if card_url in events_dict:
                target_event = events_dict[card_url]

                type_el = html_card.select_one(".event__item__category")
                if type_el:
                    target_event.event_type = type_el.text.strip().title()

                genre_el = html_card.select_one(".event__item__types")
                if genre_el:
                    target_event.genre = genre_el.text.strip().title()

        return list(events_dict.values())

    async def scrape_event_details(self, event_url: str) -> EventDetails:
        return EventDetails()