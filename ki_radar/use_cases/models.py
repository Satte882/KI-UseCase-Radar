import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords
from ki_radar.accounts.models import BusinessUnit
from ki_radar.core.models import TimeStampedModel


class UseCaseCounter(models.Model):
    id = models.BigAutoField(primary_key=True)


class UseCase(TimeStampedModel):
    class Status(models.TextChoices):
        IDEA = "idea", "Idee"
        REVIEW = "review", "Prüfung"
        PILOT = "pilot", "Pilot"
        OPERATION = "operation", "Betrieb"
        ENDED = "ended", "Beendet"

    class Level(models.TextChoices):
        LOW = "low", "Niedrig"
        MEDIUM = "medium", "Mittel"
        HIGH = "high", "Hoch"

    class Priority(models.TextChoices):
        LOW = "low", "Niedrig"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Hoch"
        CRITICAL = "critical", "Kritisch"

    class SolutionType(models.TextChoices):
        STANDARD = "standard", "Standardsoftware"
        CUSTOM = "custom", "Individuelle Anwendung"
        EMBEDDED = "embedded", "Eingebettete Systemfunktion"
        ANALYTICS = "analytics", "Analyse- oder Prognosemodell"
        GENERATIVE = "generative", "Generative KI"
        ASSISTANT = "assistant", "Assistenzsystem"
        AUTOMATION = "automation", "Automatisierungslösung"
        OTHER = "other", "Sonstige Lösung"

    class HostingType(models.TextChoices):
        INTERNAL = "internal", "Intern"
        EXTERNAL = "external", "Extern"
        HYBRID = "hybrid", "Hybrid"
        UNKNOWN = "unknown", "Noch offen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_id = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    problem_statement = models.TextField()
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.PROTECT, related_name="use_cases")
    affected_process = models.CharField(max_length=200)
    target_users = models.TextField(blank=True)
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="submitted_use_cases")
    business_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_use_cases")
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="coordinated_use_cases")
    technical_owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="technical_use_cases")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    pilot_start = models.DateField(null=True, blank=True)
    planned_pilot_end = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    solution_type = models.CharField(max_length=30, choices=SolutionType.choices, default=SolutionType.OTHER)
    hosting_type = models.CharField(max_length=20, choices=HostingType.choices, default=HostingType.UNKNOWN)
    provider = models.CharField(max_length=200, blank=True)
    product_name = models.CharField(max_length=200, blank=True)
    model_name = models.CharField(max_length=200, blank=True)
    source_systems = models.TextField(blank=True)
    data_sources = models.TextField(blank=True)
    interface_description = models.TextField(blank=True)
    intended_users = models.TextField(blank=True)
    intended_purpose = models.TextField(blank=True)

    expected_benefit = models.TextField()
    benefit_category = models.CharField(max_length=120, blank=True)
    baseline = models.TextField(blank=True)
    success_criterion = models.TextField(blank=True)
    target_value = models.CharField(max_length=200, blank=True)
    realized_result = models.TextField(blank=True)
    one_time_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    recurring_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])

    business_value = models.CharField(max_length=10, choices=Level.choices, default=Level.MEDIUM)
    technical_feasibility = models.CharField(max_length=10, choices=Level.choices, default=Level.MEDIUM)
    data_readiness = models.CharField(max_length=10, choices=Level.choices, default=Level.MEDIUM)
    risk_complexity = models.CharField(max_length=10, choices=Level.choices, default=Level.MEDIUM)

    privacy_review_required = models.BooleanField(default=False)
    security_review_required = models.BooleanField(default=False)
    legal_review_required = models.BooleanField(default=False)
    privacy_review_completed = models.BooleanField(default=False)
    security_review_completed = models.BooleanField(default=False)
    legal_review_completed = models.BooleanField(default=False)
    human_oversight = models.TextField(blank=True)
    support_responsibility = models.TextField(blank=True)

    ending_reason = models.TextField(blank=True)
    final_assessment = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    data_and_access_handling = models.TextField(blank=True)
    replacement_solution = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    history = HistoricalRecords(inherit=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "next_review_date"]),
            models.Index(fields=["business_unit", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.short_id or 'Neu'} – {self.title}"

    def save(self, *args, **kwargs):
        if not self.short_id:
            counter = UseCaseCounter.objects.create()
            self.short_id = f"KI-{counter.pk:04d}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("use_cases:detail", kwargs={"pk": self.pk})

    @property
    def recommendation(self) -> str:
        high_positive = sum(x == self.Level.HIGH for x in [self.business_value, self.technical_feasibility, self.data_readiness])
        if self.risk_complexity == self.Level.HIGH or self.data_readiness == self.Level.LOW:
            return "Weitere Klärung erforderlich"
        if high_positive >= 2 and self.risk_complexity != self.Level.HIGH:
            return "Bevorzugt prüfen"
        return "Vorläufig zurückstellen"
