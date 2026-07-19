from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from ki_radar.core.models import TimeStampedModel
from ki_radar.use_cases.models import UseCase


class Review(TimeStampedModel):
    class Decision(models.TextChoices):
        START_REVIEW = "start_review", "Prüfung starten"
        CONTINUE = "continue", "Fortführen"
        START_PILOT = "start_pilot", "Pilot starten"
        GO_LIVE = "go_live", "Produktiv setzen"
        PAUSE = "pause", "Pausieren"
        REWORK = "rework", "Überarbeiten"
        RETURN = "return", "In frühere Phase zurücksetzen"
        END = "end", "Beenden"

    use_case = models.ForeignKey(UseCase, on_delete=models.CASCADE, related_name="reviews")
    review_date = models.DateField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reviews_performed",
    )
    previous_status = models.CharField(max_length=20, choices=UseCase.Status.choices)
    new_status = models.CharField(max_length=20, choices=UseCase.Status.choices)
    decision = models.CharField(max_length=30, choices=Decision.choices)
    rationale = models.TextField()
    open_actions = models.TextField(blank=True)
    action_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="review_actions",
    )
    action_due_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    history = HistoricalRecords(inherit=True)

    class Meta:
        ordering = ["-review_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.use_case.short_id}: {self.get_decision_display()} ({self.review_date})"
