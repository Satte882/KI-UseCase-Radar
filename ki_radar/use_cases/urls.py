from django.urls import path

from . import decision_views, intake_views, origin_consistency_views, views

app_name = "use_cases"
urlpatterns = [
    path("", views.use_case_list, name="list"),
    path("new/", intake_views.use_case_intake, {"step": 1}, name="create"),
    path("new/step/<int:step>/", intake_views.use_case_intake, name="intake_step"),
    path("export.csv", views.export_csv, name="export_csv"),
    path("<uuid:pk>/", views.use_case_detail, name="detail"),
    path("<uuid:pk>/edit/", views.use_case_edit, name="edit"),
    path("<uuid:pk>/assessment/new/", decision_views.assessment_create, name="assessment_create"),
    path(
        "<uuid:pk>/decision/new/",
        decision_views.approval_decision_create,
        name="approval_decision_create",
    ),
    path(
        "decision/<int:decision_id>/second-approval/",
        decision_views.second_approval_review,
        name="second_approval_review",
    ),
    path(
        "<uuid:pk>/origin-consistency/",
        origin_consistency_views.origin_consistency_review,
        name="origin_consistency_review",
    ),
    path(
        "<uuid:pk>/origin-consistency/feedback/",
        origin_consistency_views.origin_consistency_feedback,
        name="origin_consistency_feedback",
    ),
    path("<uuid:pk>/copilot/", views.use_case_copilot, name="copilot"),
]
