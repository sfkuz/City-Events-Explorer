import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from application.scraping.service import ScraperService
from infrastructure.config import Settings

logger = logging.getLogger(__name__)

class CronService:
    def __init__(self, scraper_service: ScraperService, settings: Settings):
        self._scraper_service = scraper_service
        self._settings = settings
        self._scheduler = AsyncIOScheduler()

    def setup_jobs(self):
        self._scheduler.add_job(
            self._scraper_service.run_discovery_cycle,
            trigger='interval',
            seconds = self._settings.scraping_interval_seconds,
            id='discovery_cycle_job',
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True
        )
        self._scheduler.add_job(
            self._scraper_service.run_details_cycle,
            trigger='interval',
            minutes=5,
            id='details_cycle_job',
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True
        )
        logger.info('Cron jobs configured')

    def start(self):
        self._scheduler.start()
        logger.info('CronService started')

    def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info('CronService stopped')