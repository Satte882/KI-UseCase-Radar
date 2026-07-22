from django.apps import AppConfig


class UseCasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ki_radar.use_cases"

    def ready(self):
        from . import classification  # noqa: F401, PLC0415
        from .workflow import install  # noqa: PLC0415

        install()
