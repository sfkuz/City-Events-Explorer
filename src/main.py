from logging import getLogger
import asyncio
import sys

from app import runtime
from infrastructure.config import load_settings
from infrastructure.logging import configure_logging


logger = getLogger(__name__)

def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    logger.info(f"Starting {settings.app_name} in {settings.app_env} environment...")

    try:
        asyncio.run(runtime.run(settings))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user (KeyboardInterrupt). Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error, process shutting down: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()