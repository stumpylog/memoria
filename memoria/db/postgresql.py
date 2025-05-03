import logging

from django.db import connection

logger = logging.getLogger(__name__)


def setup_database():
    """PostgreSQL-specific database setup"""
    logger.info("Setting up PostgreSQL-specific optimizations...")

    try:
        with connection.cursor() as cursor:
            # Create BRIN index for timestamp - more efficient for large tables
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS permission_brin_timestamp_idx
            ON your_app_objectpermission USING brin (created_at);
            """)

            # Create GIN index for efficient permissions lookup
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS permission_gin_idx
            ON your_app_objectpermission USING gin (object_id, content_type_id);
            """)

            # Create a materialized view for permission summaries
            cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS permission_summary AS
            SELECT
                content_type_id,
                object_id,
                COUNT(DISTINCT user_id) as user_count,
                COUNT(DISTINCT group_id) as group_count,
                SUM(CASE WHEN can_view THEN 1 ELSE 0 END) as view_count,
                SUM(CASE WHEN can_edit THEN 1 ELSE 0 END) as edit_count
            FROM your_app_objectpermission
            GROUP BY content_type_id, object_id;
            """)

            # Add index to the materialized view
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS permission_summary_idx
            ON permission_summary(content_type_id, object_id);
            """)

        logger.info("Created PostgreSQL-specific features")
    except Exception:
        logger.exception("Error creating PostgreSQL features:")
