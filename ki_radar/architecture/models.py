from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ki_radar.accounts.models import BusinessUnit
from ki_radar.core.models import TimeStampedModel


class ValueStream(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        ACTIVE = "active", "Aktiv"
        ARCHIVED = "archived", "Archiviert"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demo_key = models.SlugField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        editable=False,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.PROTECT,
        related_name="value_streams",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_value_streams",
    )
    trigger = models.TextField(verbose_name="Auslöser")
    outcome = models.TextField(verbose_name="Ergebnis für den Empfänger")
    scope_in = models.TextField(verbose_name="Im Scope")
    scope_out = models.TextField(blank=True, verbose_name="Nicht im Scope")
    strategic_objective = models.TextField(
        blank=True,
        verbose_name="Strategisches Ziel",
    )
    stakeholders = models.TextField(blank=True, verbose_name="Stakeholder")
    constraints = models.TextField(blank=True, verbose_name="Leitplanken und Einschränkungen")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_value_streams",
    )

    class Meta:
        ordering = ["business_unit__name", "name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("architecture:value_stream_detail", kwargs={"pk": self.pk})


class ValueStreamStage(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value_stream = models.ForeignKey(
        ValueStream,
        on_delete=models.CASCADE,
        related_name="stages",
    )
    sequence = models.PositiveSmallIntegerField(verbose_name="Reihenfolge")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, verbose_name="Aktivität und Ergebnis")
    actors = models.TextField(blank=True, verbose_name="Beteiligte Rollen")
    systems = models.TextField(blank=True, verbose_name="Systeme")
    documents = models.TextField(blank=True, verbose_name="Daten und Dokumente")
    pain_points = models.TextField(blank=True, verbose_name="Probleme und Engpässe")
    baseline_metrics = models.TextField(blank=True, verbose_name="Kennzahlen und Baseline")

    class Meta:
        ordering = ["sequence", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["value_stream", "sequence"],
                name="unique_value_stream_stage_sequence",
            )
        ]

    def __str__(self) -> str:
        return f"{self.sequence}. {self.name}"

    def get_absolute_url(self):
        return self.value_stream.get_absolute_url()


class ProcessAnalysis(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        REVIEW_REQUIRED = "review_required", "Prüfbedürftig"
        VALIDATED = "validated", "Ist-Prozess validiert"
        TARGET_DEFINED = "target_defined", "Zielbild beschrieben"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage = models.ForeignKey(
        ValueStreamStage,
        on_delete=models.CASCADE,
        related_name="process_analyses",
    )
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.PositiveIntegerField(default=1, editable=False)
    source_snapshot = models.JSONField(default=dict, blank=True, editable=False)
    scope_start = models.TextField(verbose_name="Prozessstart")
    scope_end = models.TextField(verbose_name="Prozessende")
    trigger = models.TextField(verbose_name="Auslöser")
    outcome = models.TextField(verbose_name="Ergebnis")
    current_flow = models.TextField(verbose_name="Ist-Ablauf")
    roles = models.TextField(verbose_name="Rollen und Verantwortlichkeiten")
    systems = models.TextField(verbose_name="Anwendungen und Arbeitsmittel")
    data_objects = models.TextField(verbose_name="Datenobjekte und Dokumente")
    business_rules = models.TextField(blank=True, verbose_name="Geschäftsregeln")
    handoffs = models.TextField(blank=True, verbose_name="Übergaben und Schnittstellen")
    bottlenecks = models.TextField(verbose_name="Bottlenecks und Ursachen")
    exceptions = models.TextField(blank=True, verbose_name="Ausnahmen und Fehlerfälle")
    baseline_metrics = models.TextField(verbose_name="Baseline und Prozesskennzahlen")
    target_state_principles = models.TextField(
        blank=True,
        verbose_name="Prinzipien für den Soll-Prozess",
    )
    analyzed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="process_analyses",
    )

    class Meta:
        ordering = ["stage__sequence", "name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("architecture:process_analysis_detail", kwargs={"pk": self.pk})


class ProcessValidation(TimeStampedModel):
    process_analysis = models.ForeignKey(
        ProcessAnalysis,
        on_delete=models.CASCADE,
        related_name="validations",
    )
    process_version = models.PositiveIntegerField()
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="process_validations",
    )
    validator_role = models.CharField(max_length=100)
    validated_at = models.DateTimeField(default=timezone.now, editable=False)
    note = models.TextField(blank=True, verbose_name="Validierungsnotiz")
    evidence_url = models.URLField(blank=True, verbose_name="Nachweis")

    class Meta:
        ordering = ["-validated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["process_analysis", "process_version"],
                name="unique_process_validation_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.process_analysis.name} · Validierung v{self.process_version}"


class SolutionOption(TimeStampedModel):
    class OptionType(models.TextChoices):
        ORGANIZATIONAL = "organizational", "Organisatorische Änderung"
        RULE_AUTOMATION = "rule_automation", "Regelbasierte Automatisierung"
        STANDARD_SOFTWARE = "standard_software", "Standardsoftware"
        CUSTOM_SOFTWARE = "custom_software", "Individuelle Software"
        ANALYTICS_ML = "analytics_ml", "Analytics oder Machine Learning"
        GENERATIVE_AI = "generative_ai", "Generative KI"
        ASSISTANT = "assistant", "Assistenzsystem"
        NO_TECH = "no_tech", "Keine technische Lösung"
        OTHER = "other", "Sonstige Option"

    class Recommendation(models.TextChoices):
        CANDIDATE = "candidate", "Kandidat"
        PREFERRED = "preferred", "Bevorzugte Option"
        REJECTED = "rejected", "Verworfen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process_analysis = models.ForeignKey(
        ProcessAnalysis,
        on_delete=models.CASCADE,
        related_name="solution_options",
    )
    name = models.CharField(max_length=200)
    option_type = models.CharField(max_length=30, choices=OptionType.choices)
    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
        default=Recommendation.CANDIDATE,
    )
    description = models.TextField(verbose_name="Lösungsbeschreibung")
    expected_value = models.TextField(verbose_name="Erwarteter Beitrag")
    feasibility = models.CharField(
        max_length=10,
        choices=[("low", "Niedrig"), ("medium", "Mittel"), ("high", "Hoch")],
        default="medium",
        verbose_name="Machbarkeit",
    )
    data_requirements = models.TextField(blank=True, verbose_name="Datenanforderungen")
    application_impact = models.TextField(
        blank=True,
        verbose_name="Auswirkung auf Anwendungen",
    )
    integration_impact = models.TextField(blank=True, verbose_name="Integrationen")
    technology_constraints = models.TextField(
        blank=True,
        verbose_name="Technologieleitplanken",
    )
    risks = models.TextField(blank=True, verbose_name="Risiken und Nachteile")
    architecture_fit = models.TextField(
        blank=True,
        verbose_name="Begründung und Architecture Fit",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="solution_options",
    )

    class Meta:
        ordering = ["recommendation", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["process_analysis"],
                condition=models.Q(recommendation="preferred"),
                name="single_preferred_solution_per_process",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return self.process_analysis.get_absolute_url()

    @property
    def starts_ai_use_case(self) -> bool:
        non_ai_option_types = {
            self.OptionType.ORGANIZATIONAL,
            self.OptionType.RULE_AUTOMATION,
            self.OptionType.STANDARD_SOFTWARE,
            self.OptionType.NO_TECH,
        }
        return self.option_type not in non_ai_option_types


class UseCaseOrigin(TimeStampedModel):
    use_case = models.OneToOneField(
        "use_cases.UseCase",
        on_delete=models.CASCADE,
        related_name="architecture_origin",
    )
    stage = models.ForeignKey(
        ValueStreamStage,
        on_delete=models.PROTECT,
        related_name="use_case_origins",
    )
    process_analysis = models.ForeignKey(
        ProcessAnalysis,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="use_case_origins",
    )
    source_snapshot = models.JSONField(default=dict, blank=True, editable=False)
    solution_option = models.ForeignKey(
        SolutionOption,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="use_case_origins",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} aus {self.stage}"
