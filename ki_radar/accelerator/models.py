from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from ki_radar.core.models import TimeStampedModel


class CaptureSession(TimeStampedModel):
    class CaptureType(models.TextChoices):
        VALUE_STREAM = "value_stream", "Value Stream"
        USE_CASE = "use_case", "Use Case"

    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        COMPLETED = "completed", "Abgeschlossen"
        DISCARDED = "discarded", "Verworfen"
        EXPIRED = "expired", "Abgelaufen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="capture_sessions",
    )
    capture_type = models.CharField(max_length=20, choices=CaptureType.choices, db_index=True)
    working_title = models.CharField(max_length=200, blank=True)
    catalog_version = models.CharField(max_length=20)
    schema_version = models.CharField(max_length=20)
    answers = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    revision = models.PositiveIntegerField(default=0)
    answered_required_count = models.PositiveSmallIntegerField(default=0)
    required_question_count = models.PositiveSmallIntegerField(default=0)
    active_entry_seconds = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    discarded_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(
                fields=["owner", "status", "capture_type"],
                name="capture_owner_status_type_idx",
            ),
            models.Index(
                fields=["owner", "-updated_at"],
                name="capture_owner_updated_idx",
            ),
            models.Index(
                fields=["status", "expires_at"],
                name="capture_status_expires_idx",
            ),
        ]

    @property
    def progress_percent(self) -> int:
        if self.required_question_count == 0:
            return 0
        return round(self.answered_required_count / self.required_question_count * 100)

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    def __str__(self) -> str:
        label = self.working_title or self.get_capture_type_display()
        return f"{label} ({self.get_status_display()})"
