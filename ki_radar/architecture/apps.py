from django.apps import AppConfig


class ArchitectureConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ki_radar.architecture"
    verbose_name = "Discovery und Architektur"

    def ready(self):
        from . import focus  # noqa: F401
