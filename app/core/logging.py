"""
Centralized logging configuration for the application.
"""
import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("instagram_downloader")
    logger.info("Logging initialized | level=%s", logging.getLevelName(log_level))
    return logger


logger = setup_logging()
