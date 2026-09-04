import json
import logging
import asyncio
from datetime import datetime
from urllib.parse import urlparse, urljoin, quote
import re
from typing import Dict, Set, Tuple
from selectolax.parser import HTMLParser

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)

class TrojmiastoScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher
        self.chunk_size = 20
        self.max_scrolls = 5
        self.scroll_delay = 1.5
        self.max_concurrent_details = 4

    async def discover_events(self, feed_url: str) -> list[EventCard]:
        all_events_dict : Dict[str, EventCard] = {}

        logger.info(f"Scraping main page: {feed_url}")

        main_html = await self._fetcher.fetch_html(feed_url)
        main_events, _ = await self._process_page_data(main_html, feed_url)
        all_events_dict.update(main_events)

        logger.info(f"Extracted {len(main_events)} valid events from main page")

        encoded_path = quote(feed_url, safe='')
        offset = self.chunk_size

        for step in range(self.max_scrolls):
            await asyncio.sleep(self.scroll_delay)

            logger.info(f"Scraping AJAX scroll {step + 1}/{self.max_scrolls} (offset {offset})...")
            ajax_url = self._build_ajax_url(encoded_path, offset)

            try:
                chunk_events, found_urls_count = await self._process_ajax_chunk(ajax_url, feed_url)

                if not chunk_events and found_urls_count == 0:
                    logger.info(f"No events found")
                    break

                all_events_dict.update(chunk_events)
                logger.info(f"Processed offset {offset}. Total collected so far {len(all_events_dict)}")

                offset += self.chunk_size

            except Exception as e:
                logger.error(f"Error fetching offset {offset}: {e}", exc_info=True)
                continue

        return list(all_events_dict.values())


    async def scrape_event_details(self, event_url: str) -> EventDetails:
        #дописать логику деталей
        return EventDetails()

    def _build_ajax_url(self, encoded_path: str, offset: int) -> str:
        return (
            f"https://www.trojmiasto.pl/_ajax/imprezy__list_loader/?"
            f"path={encoded_path}&offset={offset}&archiveMode=0"
            f"&firstEntry=0&noService=1&mode=append"
        )

    async def _process_ajax_chunk(self, ajax_url: str, feed_url: str) -> Tuple[Dict[str, EventCard], int]:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": feed_url,
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

        ajax_response = await self._fetcher.fetch_html(ajax_url, headers=headers)

        html_content = ajax_response
        try:
            data = json.loads(ajax_response)
            if isinstance(data, dict):
                if "html" in data:
                    html_content = data["html"]
                else:
                    for val in data.values():
                        if isinstance(val, str) and "<div" in val:
                            html_content = val
                            break
        except json.JSONDecodeError:
            pass

        if not html_content or not html_content.strip():
            return {}, 0

        return await self._process_page_data(html_content, feed_url)

    async def _process_page_data(self, html_content: str, feed_url: str) -> Tuple[Dict[str, EventCard], int]:
        tree = HTMLParser(html_content)

        events_dict = self._extract_events_from_json(tree)
        self._enrich_events_from_html(tree, feed_url, events_dict)

        found_urls = set()
        for html_card in tree.css(".event__item__container"):
            link_el = html_card.css_first("a")
            if link_el and link_el.attributes.get("href"):
                raw_url = urljoin(feed_url, link_el.attributes["href"])
                found_urls.add(self._normalize_url(raw_url))

        missing_urls = found_urls - set(events_dict.keys())
        if missing_urls:
            logger.info(f"Found {len(missing_urls)} events missing JSON-LD data. Fetching details concurrently...")
            detail_events = await self._fetch_missing_details(missing_urls)
            events_dict.update(detail_events)

        return events_dict, len(found_urls)

    async def _fetch_missing_details(self, urls: Set[str]) -> Dict[str, EventCard]:
        sem = asyncio.Semaphore(self.max_concurrent_details)
        missing_events: Dict[str, EventCard] = {}

        async def fetch_detail(url: str):
            async with sem:
                try:
                    return url, await self._fetcher.fetch_html(url)
                except Exception as e:
                    logger.warning(f"Failed to fetch missing detail page {url}: {e}")
                    return url, None

        tasks = [fetch_detail(u) for u in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception) or not result[1]:
                continue

            url, resp_html = result
            detail_tree = HTMLParser(resp_html)

            detail_dict = self._extract_events_from_json(detail_tree)
            if url in detail_dict:
                missing_events[url] = detail_dict[url]

        return missing_events

    def _extract_events_from_json(self, tree: HTMLParser) -> Dict[str, EventCard]:
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