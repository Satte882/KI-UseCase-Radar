from django.apps import AppConfig


class UseCasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ki_radar.use_cases"

    def ready(self):
        from . import classification  # noqa: F401
        from .governance_journey import install as install_governance_journey
        from .primary_actions import install as install_primary_actions
        from .scale_readiness import install as install_scale_readiness
        from .value_stream_journey import install as install_value_stream_journey
        from .workflow import install

        install()
        install_value_stream_journey()
        install_governance_journey()
        install_primary_actions()
        install_scale_readiness()
