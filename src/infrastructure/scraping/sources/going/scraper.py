import logging

from application.scraping.ports import ISourceScraper, IFetcher
from application.scraping.dto import EventCard, EventDetails

logger = logging.getLogger(__name__)

class GoingScraper(ISourceScraper):
    def __init__(self, fetcher: IFetcher):
        self._fetcher = fetcher