from django.apps import AppConfig


class MemoriaAppConfig(AppConfig):
    name = "memoria"

    def ready(self):
        import memoria.signals  # noqa: F401
