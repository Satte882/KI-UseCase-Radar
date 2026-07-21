from django.contrib import admin
from django.urls import include, path

from ki_radar.core import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("ki_radar.accounts.urls")),
    path("architecture/", include("ki_radar.architecture.urls")),
    path("use-cases/", include("ki_radar.use_cases.urls")),
    path("governance/", include("ki_radar.governance.urls")),
    path("reviews/", include("ki_radar.reviews.urls")),
    path("evidence/", include("ki_radar.notifications.urls")),
    path("", include("ki_radar.reporting.urls")),
    path("health/live", health.liveness, name="health-live"),
    path("health/ready", health.readiness, name="health-ready"),
    path("health/operations", health.operational_health, name="health-operations"),
]
