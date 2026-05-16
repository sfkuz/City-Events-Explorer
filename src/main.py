import asyncio
import logging

from infrastructure.config import load_settings
from infrastructure.logging import configure_logging
from infrastructure.db.pool import create_db_pool, close_db_pool

from infrastructure.repositories.postgres_feed_repository import PostgresFeedRepository
from infrastructure.repositories.postgres_event_listings_repository import PostgresEventListingsRepository
from infrastructure.scraping.fetchers.static import StaticFetcher
from infrastructure.scraping.sources.trojmiasto.scraper import TrojmiastoScraper
from infrastructure.scraping.registry import ScraperRegistry
from application.scraping.service import ScraperService

logger = logging.getLogger(__name__)

async def _setup_test_data(pool) -> None:
    source_id = await pool.fetchval("""
                                    INSERT INTO sources (code, name, base_url, scraper_type, is_active)
                                    VALUES ('trojmiasto', 'Trojmiasto.pl', 'https://www.trojmiasto.pl', 'static',
                                            true) ON CONFLICT (code) DO
                                    UPDATE SET is_active = true
                                        RETURNING id;
                                    """)

    await pool.execute("""
                       INSERT INTO source_category_feeds (source_id, feed_url, is_active)
                       SELECT $1,
                              'https://www.trojmiasto.pl/imprezy/',
                              true WHERE NOT EXISTS (
                SELECT 1 FROM source_category_feeds WHERE source_id = $1 AND feed_url = 'https://www.trojmiasto.pl/imprezy/'
                           );
                       """, source_id)
    logger.info("Test data (Source and Feed) ensured in DB.")


async def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    logger.info("Starting Scraper Test Run...")

    pool = await create_db_pool(settings)

    try:
        await _setup_test_data(pool)

        feed_repo = PostgresFeedRepository(pool)
        listings_repo = PostgresEventListingsRepository(pool)

        fetcher = StaticFetcher()
        trojmiasto_scraper = TrojmiastoScraper(fetcher)

        registry = ScraperRegistry()
        registry.register("trojmiasto", trojmiasto_scraper)

        service = ScraperService(
            feed_repo=feed_repo,
            listings_repo=listings_repo,
            registry=registry,
            max_workers=2
        )

        await service.run_discovery_cycle()

    except Exception as e:
        logger.exception(f"Fatal error during scraping: {e}")
    finally:
        await close_db_pool(pool)
        logger.info("Scraper Test Run finished.")


def main() -> None:
    asyncio.run(run())

if __name__ == "__main__":
    main()