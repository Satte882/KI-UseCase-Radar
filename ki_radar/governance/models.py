from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from ki_radar.core.models import TimeStampedModel
from ki_radar.use_cases.models import UseCase


class GovernanceAssessment(TimeStampedModel):
    class Result(models.TextChoices):
        NO_FLAGS = "no_flags", "Keine besonderen Hinweise festgestellt"
        CLARIFICATION = "clarification", "Fachliche Klärung erforderlich"
        PRIVACY = "privacy", "Datenschutzprüfung erforderlich"
        SECURITY = "security", "Informationssicherheitsprüfung erforderlich"
        LEGAL = "legal", "Rechtliche Prüfung erforderlich"
        COMPLETED = "completed", "Prüfung abgeschlossen"

    use_case = models.ForeignKey(
        UseCase, on_delete=models.CASCADE, related_name="governance_assessments"
    )
    assessment_date = models.DateField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="governance_reviews",
    )
    basis_version = models.CharField(max_length=100)
    personal_data = models.BooleanField(default=False)
    employee_data = models.BooleanField(default=False)
    automated_person_assessment = models.BooleanField(default=False)
    influences_person_decisions = models.BooleanField(default=False)
    biometric_data = models.BooleanField(default=False)
    safety_critical = models.BooleanField(default=False)
    regulated_product = models.BooleanField(default=False)
    health_safety_rights_impact = models.BooleanField(default=False)
    external_ai_or_cloud = models.BooleanField(default=False)
    generated_external_content = models.BooleanField(default=False)
    human_oversight_planned = models.BooleanField(default=False)
    privacy_review_required = models.BooleanField(default=False)
    security_review_required = models.BooleanField(default=False)
    legal_review_required = models.BooleanField(default=False)
    result = models.CharField(max_length=30, choices=Result.choices)
    rationale = models.TextField()
    evidence_url = models.URLField(blank=True)
    next_assessment_date = models.DateField(null=True, blank=True)
    history = HistoricalRecords(inherit=True)

    class Meta:
        ordering = ["-assessment_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} – {self.assessment_date}"
