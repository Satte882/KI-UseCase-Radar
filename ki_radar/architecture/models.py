from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from ki_radar.accounts.models import BusinessUnit
from ki_radar.core.models import TimeStampedModel


class ValueStream(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        ACTIVE = "active", "Aktiv"
        ARCHIVED = "archived", "Archiviert"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    scope = models.TextField(verbose_name="Scope und Abgrenzung")
    strategic_objective = models.TextField(
        blank=True,
        verbose_name="Strategisches Ziel",
    )
    stakeholders = models.TextField(blank=True, verbose_name="Stakeholder")
    constraints = models.TextField(
        blank=True, verbose_name="Leitplanken und Einschränkungen"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
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
    baseline_metrics = models.TextField(
        blank=True, verbose_name="Kennzahlen und Baseline"
    )

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.use_case.short_id} aus {self.stage}"
