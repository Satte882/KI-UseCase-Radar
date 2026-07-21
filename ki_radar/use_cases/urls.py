from django.urls import path

from . import views

app_name = "use_cases"
urlpatterns = [
    path("", views.use_case_list, name="list"),
    path("new/", views.use_case_create, name="create"),
    path("objectives/", views.strategic_objective_list, name="objective_list"),
    path("objectives/new/", views.strategic_objective_create, name="objective_create"),
    path(
        "objectives/<int:pk>/edit/",
        views.strategic_objective_edit,
        name="objective_edit",
    ),
    path("export.csv", views.export_csv, name="export_csv"),
    path("<uuid:pk>/", views.use_case_detail, name="detail"),
    path("<uuid:pk>/edit/", views.use_case_edit, name="edit"),
    path(
        "<uuid:pk>/assessment/new/",
        views.decision_assessment_create,
        name="assessment_create",
    ),
    path(
        "<uuid:pk>/benefit-measurement/new/",
        views.benefit_measurement_create,
        name="benefit_measurement_create",
    ),
    path("<uuid:pk>/copilot/", views.use_case_copilot, name="copilot"),
]
