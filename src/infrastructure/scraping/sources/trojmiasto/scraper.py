import json
import logging
import asyncio
from datetime import datetime
from urllib.parse import urlparse, urljoin, quote
import re

from selectolax.parser import HTMLParser

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)

class TrojmiastoScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher

    async def discover_events(self, feed_url: str) -> list[EventCard]:
        all_events_dict = {}

        logger.info(f"Scraping main page: {feed_url}")
        html = await self._fetcher.fetch_html(feed_url)
        tree = HTMLParser(html)

        events_dict = self._extract_events_from_json(tree)
        logger.debug(f"Extracted {len(events_dict)} valid events from main page")

        self._enrich_events_from_html(tree, feed_url, events_dict)
        all_events_dict.update(events_dict)

        max_scrolls = 5
        offset = 20

        encoded_path = quote(feed_url, safe='')

        for i in range(max_scrolls):
            await asyncio.sleep(2)
            ajax_url = f"https://www.trojmiasto.pl/_ajax/imprezy__list_loader/?path={encoded_path}&offset={offset}&archiveMode=0&firstEntry=0&noService=1&mode=append"
            logger.info(f"Scraping AJAX scroll (offset {offset})...")

            try:
                ajax_response = await self._fetcher.fetch_html(ajax_url)

                try:
                    data = json.loads(ajax_response)
                    if isinstance(data, dict) and "html" in data:
                        ajax_response = data["html"]
                except json.JSONDecodeError:
                    pass

                ajax_tree = HTMLParser(ajax_response)
                ajax_events_dict = self._extract_events_from_json(ajax_tree)

                if not ajax_events_dict:
                    if not ajax_tree.css(".event__item__container"):
                        logger.info("Reached the end of the events list. Stopping scroll.")
                        break
                    else:
                        logger.warning(f"Cards found but no JSON-LD data at offset {offset}.")

                self._enrich_events_from_html(ajax_tree, feed_url, ajax_events_dict)
                all_events_dict.update(ajax_events_dict)
                offset += 20

            except Exception as e:
                logger.error(f"Error fetching offset {offset}: {e}", exc_info=True)
            break

        return list(all_events_dict.values())

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

                    raw_event_url = item.get("url")
                    if not raw_event_url:
                        continue
                    event_url = str(raw_event_url)
                    norm_url = self._normalize_url(event_url)

                    raw_offers = item.get("offers")
                    parsed_price = None

                    offers_list = raw_offers if isinstance(raw_offers, list) else [raw_offers] if raw_offers else []

                    prices = []
                    for offer in offers_list:
                        if isinstance(offer, dict) and "price" in offer:
                            p = offer.get("price")
                            if isinstance(p, (int, float)):
                                prices.append(int(p))
                            elif isinstance(p, str):
                                match = re.search(r'\d+(\.\d+)?', p.replace(',', '.'))
                                if match:
                                    prices.append(int(float(match.group(0))))

                    if prices:
                        parsed_price = min(prices)

                    loc = item.get("location")
                    city_text = None
                    location_name = None
                    if isinstance(loc, dict):
                        location_name = loc.get("name")
                        address = loc.get("address")
                        if isinstance(address, dict):
                            city_text = address.get("addressLocality")
                        elif isinstance(address, str):
                            city_text = address
                    elif isinstance(loc, str):
                        location_name = loc

                    perf = item.get("performer")
                    organizer_name = "Unknown"
                    if isinstance(perf, dict):
                        organizer_name = perf.get("name", "Unknown")
                    elif isinstance(perf, list) and len(perf) > 0 and isinstance(perf[0], dict):
                        organizer_name = perf[0].get("name", "Unknown")
                    elif isinstance(perf, str):
                        organizer_name = perf

                    card = EventCard(
                        external_event_id=norm_url.strip('/').split('/')[-1],
                        source_event_url=event_url,
                        title=item.get("name", "Unknown").strip(),
                        event_start_at=self._safe_parse_dt(item.get("startDate")),
                        event_end_at=self._safe_parse_dt(item.get("endDate")),
                        city_text=city_text,
                        location=location_name,
                        cover_image_url=item.get("image"),
                        price_min=parsed_price,
                        source_organizer_name=organizer_name,
                        metadata_json={},
                        detail_complete=True
                    )
                    events_dict[norm_url] = card

            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON-LD block")
            except Exception as e:
                logger.error(f"Error parsing JSON event item: {e}", exc_info=True)

        return events_dict

    def _enrich_events_from_html(self, tree: HTMLParser, feed_url: str, events_dict: dict[str, EventCard]) -> None:
        html_cards = tree.css(".event__item__container")

        for html_card in html_cards:
            try:
                link_el = html_card.css_first("a")
                if not link_el or not link_el.attributes.get("href"):
                    continue

                raw_url = urljoin(feed_url, link_el.attributes["href"])
                norm_url = self._normalize_url(raw_url)

                if norm_url in events_dict:
                    target_event = events_dict[norm_url]

                    type_el = html_card.css_first(".event__item__category")
                    if type_el:
                        target_event.event_type = type_el.text(strip=True).lower()

                    genre_el = html_card.css_first(".event__item__types")
                    if genre_el:
                        target_event.genre = genre_el.text(strip=True).lower()

            except Exception as e:
                logger.error(f"Error enriching HTML card: {e}", exc_info=True)
                continue

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