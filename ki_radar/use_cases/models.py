import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords

from ki_radar.accounts.models import BusinessUnit
from ki_radar.core.models import TimeStampedModel


class UseCaseCounter(models.Model):
    id = models.BigAutoField(primary_key=True)

    def __str__(self) -> str:
        return str(self.pk)


class StrategicObjective(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_strategic_objectives",
    )
    active_from = models.DateField(null=True, blank=True)
    active_until = models.DateField(null=True, blank=True)
    target_kpi = models.CharField(max_length=200, blank=True)
    target_value = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-is_active", "title"]
        indexes = [
            models.Index(
                fields=["is_active", "active_until"], name="use_cases_obj_active_until_idx"
            )
        ]

    def __str__(self) -> str:
        return self.title


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

    class MetricType(models.TextChoices):
        NUMBER = "number", "Zahl"
        PERCENT = "percent", "Prozent"
        DURATION = "duration", "Dauer"
        CURRENCY = "currency", "Geldbetrag"
        COUNT = "count", "Anzahl"
        RATING = "rating", "Bewertungsskala"

    class MetricDirection(models.TextChoices):
        LOWER = "lower", "Niedriger ist besser"
        HIGHER = "higher", "Höher ist besser"

    class MetricResult(models.TextChoices):
        NOT_DEFINED = "not_defined", "Metrik nicht definiert"
        NOT_MEASURED = "not_measured", "Noch nicht gemessen"
        ACHIEVED = "achieved", "Ziel erreicht"
        NOT_ACHIEVED = "not_achieved", "Ziel nicht erreicht"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_id = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    problem_statement = models.TextField()
    business_unit = models.ForeignKey(
        BusinessUnit, on_delete=models.PROTECT, related_name="use_cases"
    )
    affected_process = models.CharField(max_length=200)
    target_users = models.TextField(blank=True)
    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="submitted_use_cases",
    )
    business_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_use_cases"
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="coordinated_use_cases",
    )
    technical_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_use_cases",
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    pilot_start = models.DateField(null=True, blank=True)
    planned_pilot_end = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    solution_type = models.CharField(
        max_length=30, choices=SolutionType.choices, default=SolutionType.OTHER
    )
    hosting_type = models.CharField(
        max_length=20, choices=HostingType.choices, default=HostingType.UNKNOWN
    )
    provider = models.CharField(max_length=200, blank=True)
    product_name = models.CharField(max_length=200, blank=True)
    model_name = models.CharField(max_length=200, blank=True)
    source_systems = models.TextField(blank=True)
    data_sources = models.TextField(blank=True)
    interface_description = models.TextField(blank=True)
    intended_users = models.TextField(blank=True)
    intended_purpose = models.TextField(blank=True)

    strategic_objective = models.ForeignKey(
        StrategicObjective,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="use_cases",
    )
    strategy_contribution = models.TextField(blank=True)
    expected_benefit = models.TextField()
    benefit_category = models.CharField(max_length=120, blank=True)
    baseline = models.TextField(blank=True)
    success_criterion = models.TextField(blank=True)
    target_value = models.CharField(max_length=200, blank=True)
    realized_result = models.TextField(blank=True)

    metric_name = models.CharField(max_length=200, blank=True, verbose_name="Primäre Erfolgsmetrik")
    metric_type = models.CharField(
        max_length=20, choices=MetricType.choices, blank=True, verbose_name="Metriktyp"
    )
    metric_direction = models.CharField(
        max_length=10,
        choices=MetricDirection.choices,
        blank=True,
        verbose_name="Optimierungsrichtung",
    )
    metric_unit = models.CharField(max_length=80, blank=True, verbose_name="Einheit")
    metric_baseline = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Baseline-Wert",
    )
    metric_target = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Zielwert",
    )
    metric_actual = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Gemessener Ist-Wert",
    )
    metric_measurement_method = models.TextField(blank=True, verbose_name="Messmethode")
    metric_measurement_period = models.CharField(
        max_length=200, blank=True, verbose_name="Messzeitraum"
    )
    metric_measured_at = models.DateField(null=True, blank=True, verbose_name="Messdatum")
    metric_evidence_url = models.URLField(blank=True, verbose_name="Messnachweis")

    one_time_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    recurring_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )

    business_value = models.CharField(max_length=10, choices=Level.choices, default=Level.MEDIUM)
    technical_feasibility = models.CharField(
        max_length=10, choices=Level.choices, default=Level.MEDIUM
    )
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
            models.Index(
                fields=["status", "next_review_date"], name="use_cases_u_status_166548_idx"
            ),
            models.Index(
                fields=["business_unit", "status"], name="use_cases_u_busines_130cef_idx"
            ),
            models.Index(
                fields=["strategic_objective", "status"], name="usecase_strategy_status_idx"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.short_id or 'Neu'} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.short_id:
            counter = UseCaseCounter.objects.create()
            self.short_id = f"KI-{counter.pk:04d}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("use_cases:detail", kwargs={"pk": self.pk})

    @property
    def metric_result(self) -> str:
        if not all([self.metric_name, self.metric_direction]) or self.metric_target is None:
            return self.MetricResult.NOT_DEFINED
        if self.metric_actual is None:
            return self.MetricResult.NOT_MEASURED
        if self.metric_direction == self.MetricDirection.LOWER:
            achieved = self.metric_actual <= self.metric_target
        else:
            achieved = self.metric_actual >= self.metric_target
        return self.MetricResult.ACHIEVED if achieved else self.MetricResult.NOT_ACHIEVED

    @property
    def metric_result_label(self) -> str:
        return self.MetricResult(self.metric_result).label

    @property
    def metric_delta(self) -> Decimal | None:
        if self.metric_actual is None or self.metric_baseline is None:
            return None
        return self.metric_actual - self.metric_baseline

    @property
    def recommendation(self) -> str:
        high_positive = sum(
            x == self.Level.HIGH
            for x in [self.business_value, self.technical_feasibility, self.data_readiness]
        )
        if self.risk_complexity == self.Level.HIGH or self.data_readiness == self.Level.LOW:
            return "Weitere Klärung erforderlich"
        if high_positive >= 2 and self.risk_complexity != self.Level.HIGH:
            return "Bevorzugt prüfen"
        return "Vorläufig zurückstellen"


class DecisionAssessment(TimeStampedModel):
    class Confidence(models.TextChoices):
        LOW = "low", "Niedrig"
        MEDIUM = "medium", "Mittel"
        HIGH = "high", "Hoch"

    use_case = models.ForeignKey(
        UseCase, on_delete=models.CASCADE, related_name="decision_assessments"
    )
    version = models.PositiveIntegerField()
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="decision_assessments",
    )
    assessment_date = models.DateField()

    business_value = models.CharField(max_length=10, choices=UseCase.Level.choices)
    business_value_confidence = models.CharField(max_length=10, choices=Confidence.choices)
    business_value_rationale = models.TextField()
    business_value_evidence_url = models.URLField(blank=True)

    strategic_fit = models.CharField(max_length=10, choices=UseCase.Level.choices)
    strategic_fit_confidence = models.CharField(max_length=10, choices=Confidence.choices)
    strategic_fit_rationale = models.TextField()
    strategic_fit_evidence_url = models.URLField(blank=True)

    technical_feasibility = models.CharField(max_length=10, choices=UseCase.Level.choices)
    technical_feasibility_confidence = models.CharField(max_length=10, choices=Confidence.choices)
    technical_feasibility_rationale = models.TextField()
    technical_feasibility_evidence_url = models.URLField(blank=True)

    data_readiness = models.CharField(max_length=10, choices=UseCase.Level.choices)
    data_readiness_confidence = models.CharField(max_length=10, choices=Confidence.choices)
    data_readiness_rationale = models.TextField()
    data_readiness_evidence_url = models.URLField(blank=True)

    risk_complexity = models.CharField(max_length=10, choices=UseCase.Level.choices)
    risk_complexity_confidence = models.CharField(max_length=10, choices=Confidence.choices)
    risk_complexity_rationale = models.TextField()
    risk_complexity_evidence_url = models.URLField(blank=True)

    overall_rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["use_case", "version"], name="unique_assessment_version_per_use_case"
            )
        ]
        indexes = [
            models.Index(
                fields=["use_case", "-assessment_date"],
                name="use_cases_assessment_date_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} – Bewertung v{self.version}"

    @property
    def minimum_confidence(self) -> str:
        values = [
            self.business_value_confidence,
            self.strategic_fit_confidence,
            self.technical_feasibility_confidence,
            self.data_readiness_confidence,
            self.risk_complexity_confidence,
        ]
        order = {self.Confidence.LOW: 0, self.Confidence.MEDIUM: 1, self.Confidence.HIGH: 2}
        return min(values, key=order.get)

    @property
    def minimum_confidence_label(self) -> str:
        return self.Confidence(self.minimum_confidence).label

    @property
    def criterion_rows(self) -> list[dict]:
        fields = [
            ("Business Value", "business_value"),
            ("Strategischer Fit", "strategic_fit"),
            ("Technische Machbarkeit", "technical_feasibility"),
            ("Datenreife", "data_readiness"),
            ("Risiko und Komplexität", "risk_complexity"),
        ]
        return [
            {
                "label": label,
                "rating": getattr(self, f"get_{name}_display")(),
                "confidence": getattr(self, f"get_{name}_confidence_display")(),
                "rationale": getattr(self, f"{name}_rationale"),
                "evidence_url": getattr(self, f"{name}_evidence_url"),
            }
            for label, name in fields
        ]


class BenefitMeasurement(TimeStampedModel):
    use_case = models.ForeignKey(
        UseCase, on_delete=models.CASCADE, related_name="benefit_measurements"
    )
    measured_at = models.DateField(db_index=True)
    period = models.CharField(max_length=200)
    actual_value = models.DecimalField(max_digits=14, decimal_places=4)
    method = models.TextField()
    evidence_url = models.URLField()
    variance_reason = models.TextField(blank=True)
    decision_consequence = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="benefit_measurements",
    )

    class Meta:
        ordering = ["-measured_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["use_case", "-measured_at"], name="use_cases_benefit_date_idx"
            )
        ]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} – {self.measured_at}"

    @property
    def result(self) -> str:
        if self.use_case.metric_target is None or not self.use_case.metric_direction:
            return UseCase.MetricResult.NOT_DEFINED
        if self.use_case.metric_direction == UseCase.MetricDirection.LOWER:
            achieved = self.actual_value <= self.use_case.metric_target
        else:
            achieved = self.actual_value >= self.use_case.metric_target
        return UseCase.MetricResult.ACHIEVED if achieved else UseCase.MetricResult.NOT_ACHIEVED

    @property
    def result_label(self) -> str:
        return UseCase.MetricResult(self.result).label

    @property
    def delta_from_baseline(self) -> Decimal | None:
        if self.use_case.metric_baseline is None:
            return None
        return self.actual_value - self.use_case.metric_baseline
