from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from ki_radar.core.models import TimeStampedModel


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
    non_functional_requirements = models.TextField(
        verbose_name="Nichtfunktionale Anforderungen"
    )
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

    def get_absolute_url(self):
        return reverse("delivery:package_detail", kwargs={"pk": self.pk})
