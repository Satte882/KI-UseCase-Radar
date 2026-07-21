from django.urls import path

from . import views

app_name = "delivery"
urlpatterns = [
    path("", views.package_list, name="package_list"),
    path("use-cases/<uuid:use_case_id>/new/", views.package_create, name="package_create"),
    path("<uuid:pk>/", views.package_detail, name="package_detail"),
    path("<uuid:pk>/edit/", views.package_update, name="package_update"),
    path("<uuid:pk>/ready/", views.package_mark_ready, name="package_mark_ready"),
    path("<uuid:pk>/handover/", views.package_handover, name="package_handover"),
    path("<uuid:pk>/export.md", views.package_export_markdown, name="package_export_markdown"),
]
