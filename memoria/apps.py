from django.apps import AppConfig
from django.conf import settings


class MemoriaAppConfig(AppConfig):
    name = "memoria"

    def ready(self):
        import importlib

        try:
            # This will import either db.postgresql or db.sqlite based on settings
            importlib.import_module(settings.DB_SPECIFIC_MODULE)
        except ImportError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Could not import database module: {settings.DB_SPECIFIC_MODULE}")

        from memoria.signals.handlers import cleanup_files_on_delete  # noqa: F401
        from memoria.signals.handlers import handle_create_user_profile  # noqa: F401
        from memoria.signals.handlers import mark_image_as_dirty  # noqa: F401
        from memoria.signals.handlers import mark_images_as_dirty_on_fk_change  # noqa: F401
        from memoria.signals.handlers import mark_images_as_dirty_on_m2m_change  # noqa: F401
