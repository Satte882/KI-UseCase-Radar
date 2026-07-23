from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from ki_radar.core.models import TimeStampedModel

DELIVERY_SECTION_DEFINITIONS = (
    ("problem_and_target", "Problem und Ziel"),
    ("scope_and_users", "Scope, Nutzer und MVP"),
    ("solution_direction", "Gewählte Lösungsrichtung"),
    ("architecture_and_data", "System-, Daten- und Integrationskontext"),
    ("requirements_and_governance", "Anforderungen und Governance"),
    ("acceptance_and_measurement", "Akzeptanz und Erfolgsmessung"),
    ("delivery_control", "Risiken, Abhängigkeiten und Umsetzungsstart"),
)

SECTION_REVIEW_REQUIREMENTS = {
    "problem_and_target": frozenset({"business"}),
    "scope_and_users": frozenset({"business"}),
    "solution_direction": frozenset({"business", "technical"}),
    "architecture_and_data": frozenset({"technical"}),
    "requirements_and_governance": frozenset({"technical"}),
    "acceptance_and_measurement": frozenset({"business"}),
    "delivery_control": frozenset({"business", "technical"}),
}


class DeliveryPackage(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        READY = "ready", "Bereit zur Übergabe"
        HANDED_OVER = "handed_over", "Übergeben"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    use_case = models.ForeignKey(
        "use_cases.UseCase",
        on_delete=models.CASCADE,
        related_name="delivery_packages",
    )
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    readiness_schema_version = models.PositiveSmallIntegerField(default=1)
    generated_from_decision = models.ForeignKey(
        "use_cases.ApprovalDecision",
        on_delete=models.PROTECT,
        related_name="delivery_packages",
    )
    problem_context = models.TextField(verbose_name="Problem und Geschäftskontext")
    target_outcome = models.TextField(verbose_name="Ziel und erwartetes Ergebnis")
    in_scope = models.TextField(verbose_name="Im Scope")
    out_of_scope = models.TextField(verbose_name="Nicht im Scope")
    users_and_scenarios = models.TextField(verbose_name="Nutzer und Nutzungsszenarien")
    solution_outline = models.TextField(verbose_name="Lösungsrahmen und Zielbild")
    system_context = models.TextField(verbose_name="System- und Anwendungskontext")
    data_context = models.TextField(verbose_name="Datenobjekte und Datenquellen")
    integrations = models.TextField(blank=True, verbose_name="Schnittstellen und Integrationen")
    functional_requirements = models.TextField(verbose_name="Funktionale Anforderungen")
    non_functional_requirements = models.TextField(verbose_name="Nichtfunktionale Anforderungen")
    security_privacy_requirements = models.TextField(
        verbose_name="Security-, Datenschutz- und Rechtsanforderungen"
    )
    human_oversight = models.TextField(verbose_name="Menschliche Aufsicht")
    logging_and_audit = models.TextField(verbose_name="Logging und Nachvollziehbarkeit")
    operations_and_support = models.TextField(verbose_name="Betrieb und Support")
    mvp_scope = models.TextField(verbose_name="MVP-Scope")
    acceptance_criteria = models.TextField(verbose_name="Akzeptanzkriterien")
    test_scenarios = models.TextField(verbose_name="Testfälle und Qualitätssicherung")
    measurement_plan = models.TextField(verbose_name="Erfolgsmessung und Pilot")
    dependencies = models.TextField(blank=True, verbose_name="Abhängigkeiten")
    risks = models.TextField(blank=True, verbose_name="Risiken")
    assumptions = models.TextField(blank=True, verbose_name="Annahmen")
    architecture_decisions = models.TextField(
        blank=True,
        verbose_name="Architekturentscheidungen und Leitplanken",
    )
    initial_backlog = models.TextField(verbose_name="Initiales Backlog")
    external_delivery_url = models.URLField(blank=True, verbose_name="Delivery-System")
    handover_notes = models.TextField(blank=True, verbose_name="Übergabehinweise")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_delivery_packages",
    )
    handed_over_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="handed_over_delivery_packages",
    )
    handed_over_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["use_case", "version"],
                name="unique_delivery_package_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} - Delivery v{self.version}"

    def save(self, *args, **kwargs):
        if self.pk:
            previous_status = (
                type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()
            )
            if previous_status == self.Status.HANDED_OVER:
                raise ValidationError(
                    "Eine übergebene Delivery-Package-Version ist unveränderlich."
                )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("delivery:package_detail", kwargs={"pk": self.pk})


class DeliverySectionReview(TimeStampedModel):
    class Section(models.TextChoices):
        PROBLEM_AND_TARGET = "problem_and_target", "Problem und Ziel"
        SCOPE_AND_USERS = "scope_and_users", "Scope, Nutzer und MVP"
        SOLUTION_DIRECTION = "solution_direction", "Gewählte Lösungsrichtung"
        ARCHITECTURE_AND_DATA = (
            "architecture_and_data",
            "System-, Daten- und Integrationskontext",
        )
        REQUIREMENTS_AND_GOVERNANCE = (
            "requirements_and_governance",
            "Anforderungen und Governance",
        )
        ACCEPTANCE_AND_MEASUREMENT = (
            "acceptance_and_measurement",
            "Akzeptanz und Erfolgsmessung",
        )
        DELIVERY_CONTROL = (
            "delivery_control",
            "Risiken, Abhängigkeiten und Umsetzungsstart",
        )

    class ContentOrigin(models.TextChoices):
        INHERITED = "inherited", "Übernommen"
        MIXED = "mixed", "Übernommen und ergänzt"
        NEW = "new", "Neu für Delivery"
        NOT_APPLICABLE = "not_applicable", "Nicht relevant"

    class ReviewStatus(models.TextChoices):
        NEEDS_REVIEW = "needs_review", "Prüfung erforderlich"
        CONFIRMED = "confirmed", "Bestätigt"
        BLOCKED = "blocked", "Blockiert"
        NOT_APPLICABLE = "not_applicable", "Nicht relevant"

    delivery_package = models.ForeignKey(
        DeliveryPackage,
        on_delete=models.CASCADE,
        related_name="section_reviews",
    )
    section_key = models.CharField(max_length=50, choices=Section.choices)
    content_origin = models.CharField(
        max_length=30,
        choices=ContentOrigin.choices,
        default=ContentOrigin.NEW,
    )
    review_status = models.CharField(
        max_length=30,
        choices=ReviewStatus.choices,
        default=ReviewStatus.NEEDS_REVIEW,
    )
    source_manifest = models.JSONField(default=dict, blank=True)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_delivery_sections",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    business_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="business_confirmed_delivery_sections",
    )
    business_confirmed_at = models.DateTimeField(null=True, blank=True)
    technical_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_confirmed_delivery_sections",
    )
    technical_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["delivery_package", "section_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["delivery_package", "section_key"],
                name="unique_delivery_section_review",
            )
        ]

    def __str__(self) -> str:
        return f"{self.delivery_package} - {self.get_section_key_display()}"

    @property
    def required_confirmations(self) -> frozenset[str]:
        return SECTION_REVIEW_REQUIREMENTS[self.section_key]

    @property
    def confirmations_complete(self) -> bool:
        required = self.required_confirmations
        return not (
            ("business" in required and self.business_confirmed_at is None)
            or ("technical" in required and self.technical_confirmed_at is None)
        )
