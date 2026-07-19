from django.urls import path
from .views import dashboard

app_name = "reporting"
urlpatterns = [
    path("", dashboard, name="dashboard"),
]
