import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

from domain.events.entities import Event
from app.runtime import run


def scrape_events(url: str) -> list[Event]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    print(f"[{datetime.now().strftime('%H:%M:%S')}]  {url}")
    response = requests.get(url, headers=headers)
    print(f"Статус ответа от сайта: {response.status_code}")  # Должен быть 200

    soup = BeautifulSoup(response.text, 'lxml')
    events_dict = {}

    json_scripts = soup.find_all("script", type="application/ld+json")
    print(f"found JSON blocks: {len(json_scripts)}")

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

                    start_dt = datetime.fromisoformat(item.get("startDate"))
                    end_dt_str = item.get("endDate")
                    end_dt = datetime.fromisoformat(end_dt_str) if end_dt_str else None

                    # Собираем
                    event_obj = Event(
                        title=item.get("name", "Unknown"),
                        description=item.get("description"),
                        location=item.get("location", {}).get("name"),
                        start_at=start_dt,
                        end_at=end_dt,
                        organizer_name=item.get("performer", {}).get("name", "Unknown"),
                        url=event_url,
                        cover_image_url=item.get("image"),
                        price=int(item["offers"]["price"]) if item.get("offers", {}).get("price") is not None else None
                    )
                    events_dict[event_url] = event_obj
                    print(f"json reading complete: {event_obj.title}")

        except json.JSONDecodeError as e:
            print(f"error reading: {e}")
        except Exception as e:
            print(f"error building: {e}")

    print(f"after first step: {len(events_dict)} events")

    html_cards = soup.select(".event__item__container")
    print(f"in HTML found cards: {len(html_cards)}")

    for card in html_cards:
        link_el = card.select_one("a")
        if not link_el:
            continue

        card_url = link_el.get("href")
        if card_url and card_url.startswith('/'):
            card_url = f"https://{url.split('/')[2]}{card_url}"

        if card_url in events_dict:
            target_event = events_dict[card_url]

            type_el = card.select_one(".event__item__category")
            if type_el:
                target_event.event_type = type_el.text.strip().title()

    return list(events_dict.values())

async def run():
    TARGET_URL = "https://www.trojmiasto.pl/imprezy/"

    print("sending")
    events = await asyncio.to_thread(scrape_events, TARGET_URL)

    print("\n--- 🟢 results ---\n")
    for e in events[:5]:
        print(f" {e.title}")
        print(f"type: {e.event_type}")
        print(f"genre:      {e.genre}")
        print(f"url:     {e.url}")
        print("-" * 40)

    print(f"complete: {len(events)}")



def main() -> None:
    asyncio.run(run())

if __name__ == "__main__":
    main()