from django.urls import path

from . import views
from .models import CaptureSession

app_name = "accelerator"

urlpatterns = [
    path(
        "value-stream/start/",
        views.start_capture,
        {"capture_type": CaptureSession.CaptureType.VALUE_STREAM},
        name="value_stream_start",
    ),
    path(
        "use-case/start/",
        views.start_capture,
        {"capture_type": CaptureSession.CaptureType.USE_CASE},
        name="use_case_start",
    ),
    path(
        "<uuid:session_id>/step/<int:step>/",
        views.capture_step,
        name="capture_step",
    ),
    path(
        "<uuid:session_id>/review/",
        views.capture_review,
        name="capture_review",
    ),
    path(
        "<uuid:session_id>/discard/",
        views.capture_discard,
        name="capture_discard",
    ),
]
