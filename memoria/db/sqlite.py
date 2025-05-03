import logging

logger = logging.getLogger(__name__)


def setup_database():
    """SQLite-specific database setup (minimal setup needed)"""
    logger.info("Setting up SQLite-specific configuration...")

    # SQLite doesn't need most of the PostgreSQL optimizations
    # But we can add some SQLite-specific optimizations if needed
    logger.info("Enabling SQLite WAL mode for better concurrency...")

    try:
        from django.db import connection

        with connection.cursor() as cursor:
            # Enable Write-Ahead Logging mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")

            # Other helpful SQLite optimizations
            cursor.execute("PRAGMA synchronous=NORMAL;")  # Boost performance a bit
            cursor.execute("PRAGMA cache_size=-102400;")  # Use 100MB cache (in KiB)

        logger.info("SQLite optimizations applied")
    except Exception:
        logger.exception("Error setting up SQLite")
