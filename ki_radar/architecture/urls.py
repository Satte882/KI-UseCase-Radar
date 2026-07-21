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
    path(
        "stages/<uuid:stage_id>/processes/new/",
        views.process_analysis_create,
        name="process_analysis_create",
    ),
    path(
        "processes/<uuid:pk>/",
        views.process_analysis_detail,
        name="process_analysis_detail",
    ),
    path(
        "processes/<uuid:pk>/edit/",
        views.process_analysis_update,
        name="process_analysis_update",
    ),
    path(
        "processes/<uuid:process_analysis_id>/options/new/",
        views.solution_option_create,
        name="solution_option_create",
    ),
    path(
        "options/<uuid:pk>/edit/",
        views.solution_option_update,
        name="solution_option_update",
    ),
    path(
        "options/<uuid:pk>/start-use-case/",
        views.solution_option_start_use_case,
        name="solution_option_start_use_case",
    ),
]
