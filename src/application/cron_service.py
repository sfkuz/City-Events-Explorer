import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from application.scraping.service import ScraperService

logger = logging.getLogger(__name__)

class CronService:
    def __init__(self, scraper_service: ScraperService):
        self._scraper_service = scraper_service
        self._scheduler = AsyncIOScheduler()

    def setup_jobs(self):
        self._scheduler.add_job(
            self._scraper_service.run_discovery_cycle,
            trigger='interval',
            hours = 4,
            id='discovery_cycle_job',
            replace_existing=True
        )
        logger.info('Cron jobs configured')

    def start(self):
        self._scheduler.start()
        logger.info('CronService started')

    def stop(self):
        self._scheduler.shutdown()