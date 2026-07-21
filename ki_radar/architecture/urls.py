from django.urls import path

from . import views

app_name = "architecture"
urlpatterns = [
    path("", views.value_stream_list, name="value_stream_list"),
    path("new/", views.value_stream_create, name="value_stream_create"),
    path("<uuid:pk>/", views.value_stream_detail, name="value_stream_detail"),
    path("<uuid:pk>/edit/", views.value_stream_update, name="value_stream_update"),
    path(
        "<uuid:value_stream_id>/stages/new/",
        views.stage_create,
        name="stage_create",
    ),
    path("stages/<uuid:pk>/edit/", views.stage_update, name="stage_update"),
    path(
        "stages/<uuid:pk>/start-use-case/",
        views.stage_start_use_case,
        name="stage_start_use_case",
    ),
]
