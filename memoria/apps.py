from django.apps import AppConfig


class MemoriaAppConfig(AppConfig):
    name = "memoria"

    def ready(self):
        from memoria.signals.handlers import cleanup_files_on_delete  # noqa: F401
        from memoria.signals.handlers import handle_create_user_profile  # noqa: F401
        from memoria.signals.handlers import mark_image_as_dirty  # noqa: F401
        from memoria.signals.handlers import mark_images_as_dirty_on_fk_change  # noqa: F401
        from memoria.signals.handlers import mark_images_as_dirty_on_m2m_change  # noqa: F401
