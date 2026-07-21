from django.urls import path

from .views import dashboard, portfolio

app_name = "reporting"
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("portfolio/", portfolio, name="portfolio"),
]
