from django.urls import path

from . import views

app_name = "use_cases"
urlpatterns = [
    path("", views.use_case_list, name="list"),
    path("new/", views.use_case_create, name="create"),
    path("export.csv", views.export_csv, name="export_csv"),
    path("<uuid:pk>/", views.use_case_detail, name="detail"),
    path("<uuid:pk>/edit/", views.use_case_edit, name="edit"),
    path("<uuid:pk>/copilot/", views.use_case_copilot, name="copilot"),
]
