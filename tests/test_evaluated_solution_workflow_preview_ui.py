from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.accelerator.models import SolutionGenerationRun, SolutionQualityRun
from ki_radar.accelerator.solution_critic_contract import validate_solution_critic_payload
from ki_radar.accelerator.solution_generation_contract import (
    GENERATED_OPTION_FIELDS,
    GENERATION_PROMPT_VERSION,
    GENERATION_SCHEMA_VERSION,
    OPTION_LANES,
)
from ki_radar.accelerator.solution_generation_sources import (
    build_solution_generation_source_context,
)
from ki_radar.accelerator.solution_quality_snapshot import build_solution_quality_snapshot
from ki_radar.accelerator.solution_quality_versions import (
    CRITIC_PROMPT_VERSION,
    CRITIC_SCHEMA_VERSION,
)
from ki_radar.architecture.models import ProcessAnalysis, ValueStream, ValueStreamStage

FIELD_SOURCES = {
    "name": "process.current_flow",
    "description": "process.current_flow",
    "expected_value": "process.bottlenecks",
    "bottleneck_coverage": "process.bottlenecks",
    "data_requirements": "process.data_objects",
    "application_impact": "process.systems",
    "integration_impact": "process.systems",
    "technology_constraints": "value_stream.constraints",
    "risks": "process.exceptions",
    "architecture_fit": "process.target_state_principles",
}


def _make_process(owner, business_unit) -> ProcessAnalysis:
    stream = ValueStream.objects.create(
        name="Beschaffung AP9 Preview",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Freigegebener Bedarf",
        outcome="Bestellung ausgelöst",
        scope_in="Bedarf bis Bestellung",
        strategic_objective="Durchlaufzeit reduzieren",
        constraints="EU-Datenhaltung und menschliche Freigabe",
    )
    stage = ValueStreamStage.objects.create(
        value_stream=stream,
        sequence=2,
        name="Angebote vergleichen",
        description="Angebote fachlich vergleichen",
        actors="Einkauf",
        systems="ERP",
        documents="Angebote",
        pain_points="Manueller Vergleich",
        baseline_metrics="11 Minuten pro Vergleich",
    )
    return ProcessAnalysis.objects.create(
        stage=stage,
        name="Angebotsvergleich AP9",
        scope_start="Angebote liegen vor",
        scope_end="Auswahl ist dokumentiert",
        trigger="Angebotsfrist endet",
        outcome="Nachvollziehbare Auswahl",
        current_flow="Angebote werden manuell gegenübergestellt.",
        roles="Einkauf und Fachbereich",
        systems="ERP und Dateiablage",
        data_objects="Angebote und Kriterienkatalog",
        business_rules="Vier-Augen-Prinzip bei Freigabe",
        handoffs="Einkauf übergibt an Fachbereich",
        bottlenecks="Manuelle Übertragung verursacht Wartezeit.",
        exceptions="Fehlende Pflichtangaben werden nachgefordert.",
        baseline_metrics="11 Minuten pro Vergleich",
        target_state_principles="Nachvollziehbar und assistierend",
        analyzed_by=owner,
    )


def _statement(text: str, source_id: str) -> dict[str, object]:
    return {
        "text": text,
        "source_ids": [source_id],
        "assumptions": [],
        "open_evidence": [],
        "uncertainty": {
            "level": "low",
            "reason": "Direkt aus der angegebenen Quelle abgeleitet.",
        },
    }


def _make_run(owner, business_unit) -> SolutionGenerationRun:
    process = _make_process(owner, business_unit)
    source_context = build_solution_generation_source_context(process)
    options: dict[str, dict[str, object]] = {}
    for lane in OPTION_LANES:
        option: dict[str, object] = {}
        for field_name in GENERATED_OPTION_FIELDS:
            option[field_name] = _statement(
                f"{lane}: {field_name.replace('_', ' ')}",
                FIELD_SOURCES[field_name],
            )
        options[lane] = option
    preview_payload = {
        "schema_version": GENERATION_SCHEMA_VERSION,
        "prompt_version": GENERATION_PROMPT_VERSION,
        "source_context": source_context.provider_payload(),
        "options": options,
        "edits": {},
    }
    return SolutionGenerationRun.objects.create(
        process_analysis=process,
        process_version=source_context.process_version,
        source_hash=source_context.source_hash,
        requested_by=owner,
        status=SolutionGenerationRun.Status.SUCCESS,
        provider="openrouter",
        model_name="test/generator",
        prompt_version=GENERATION_PROMPT_VERSION,
        generation_schema_version=GENERATION_SCHEMA_VERSION,
        started_at=timezone.now() - timedelta(seconds=1),
        finished_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=1),
        preview_payload=preview_payload,
    )


def _make_initial_critic(
    run: SolutionGenerationRun,
    *,
    repairable: bool,
) -> SolutionQualityRun:
    source_context = build_solution_generation_source_context(run.process_analysis)
    snapshot = build_solution_quality_snapshot(
        preview_payload=run.preview_payload,
        source_context=source_context,
    )
    finding = {
        "criterion": "bottleneck_fit",
        "option": "assistant",
        "field": "bottleneck_coverage",
        "finding": "Der Engpassbezug muss präziser aus der dokumentierten Ursache hergeleitet werden.",
        "source_ids": ["process.bottlenecks"],
        "repairable": repairable,
        "related_targets": [],
    }
    result_payload = validate_solution_critic_payload(
        {
            "schema_version": CRITIC_SCHEMA_VERSION,
            "prompt_version": CRITIC_PROMPT_VERSION,
            "findings": [finding],
        },
        source_context,
    )
    return SolutionQualityRun.objects.create(
        solution_generation_run=run,
        requested_by=run.requested_by,
        step_type=SolutionQualityRun.StepType.INITIAL_CRITIC,
        status=SolutionQualityRun.Status.SUCCESS,
        provider="openrouter",
        model_name="test/critic",
        prompt_version=CRITIC_PROMPT_VERSION,
        output_schema_version=CRITIC_SCHEMA_VERSION,
        input_hash=snapshot.snapshot_hash,
        started_at=timezone.now() - timedelta(seconds=1),
        finished_at=timezone.now(),
        result_payload=result_payload,
    )


@pytest.mark.django_db
def test_preview_shows_repairable_finding_and_one_shot_action_without_provider_call(
    client,
    owner,
    business_unit,
):
    run = _make_run(owner, business_unit)
    _make_initial_critic(run, repairable=True)
    client.force_login(owner)

    with (
        patch("ki_radar.accelerator.solution_critic_service.request_openrouter") as critic_provider,
        patch("ki_radar.accelerator.solution_repair_service.request_openrouter") as repair_provider,
    ):
        response = client.get(reverse("accelerator:solution_generation_preview", args=[run.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "KI-Qualitätsprüfung" in content
    assert "Qualitätsprüfung – keine Bewertung oder Lösungsempfehlung." in content
    assert "Passung zum Engpass" in content
    assert "Bottleneck-Abdeckung" in content
    assert "Engpassbezug muss präziser" in content
    assert "Maschinell reparierbar" in content
    assert "Reparierbare Findings einmalig korrigieren" in content
    critic_provider.assert_not_called()
    repair_provider.assert_not_called()


@pytest.mark.django_db
def test_nonrepairable_findings_go_directly_to_human_review(client, owner, business_unit):
    run = _make_run(owner, business_unit)
    _make_initial_critic(run, repairable=False)
    client.force_login(owner)

    response = client.get(reverse("accelerator:solution_generation_preview", args=[run.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Manuell prüfen" in content
    assert "Human Review" in content
    assert "Reparierbare Findings einmalig korrigieren" not in content
    assert "Bearbeitungen speichern" in content
    assert "ausgewählte KI-Lösungsoptionen hinzufügen" in content.lower()


@pytest.mark.django_db
def test_cas_stale_preview_shows_explicit_message_and_never_calls_provider(
    client,
    owner,
    business_unit,
):
    run = _make_run(owner, business_unit)
    _make_initial_critic(run, repairable=True)
    payload = dict(run.preview_payload)
    payload["edits"] = {"assistant": {"description": "Nach Critic manuell präzisiert."}}
    run.preview_payload = payload
    run.save(update_fields=["preview_payload", "updated_at"])
    client.force_login(owner)

    with patch(
        "ki_radar.accelerator.solution_repair_service.request_openrouter"
    ) as repair_provider:
        response = client.get(reverse("accelerator:solution_generation_preview", args=[run.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Vorschau wurde seit der Prüfung bearbeitet, Reparatur nicht mehr möglich." in content
    assert "Reparierbare Findings einmalig korrigieren" not in content
    assert "Bearbeitungen speichern" in content
    repair_provider.assert_not_called()


@pytest.mark.django_db
def test_repair_endpoint_invokes_existing_service_once_and_redirects_to_quality_section(
    client,
    owner,
    business_unit,
):
    run = _make_run(owner, business_unit)
    _make_initial_critic(run, repairable=True)
    client.force_login(owner)

    with patch(
        "ki_radar.accelerator.solution_generation_views.run_targeted_solution_repair",
        return_value=SimpleNamespace(status=SolutionQualityRun.Status.SUCCESS),
    ) as repair_service:
        response = client.post(reverse("accelerator:solution_generation_repair", args=[run.pk]))

    assert response.status_code == 302
    assert response.url.endswith("#solution-generation-quality")
    repair_service.assert_called_once_with(
        solution_generation_run_id=run.pk,
        actor=owner,
    )


@pytest.mark.django_db
def test_source_stale_repair_request_is_rejected_before_service_call(
    client,
    owner,
    business_unit,
):
    run = _make_run(owner, business_unit)
    _make_initial_critic(run, repairable=True)
    process = run.process_analysis
    process.current_flow = "Der fachliche Quellstand wurde nach der Prüfung geändert."
    process.save(update_fields=["current_flow", "updated_at"])
    client.force_login(owner)

    with patch(
        "ki_radar.accelerator.solution_generation_views.run_targeted_solution_repair"
    ) as repair_service:
        response = client.post(reverse("accelerator:solution_generation_repair", args=[run.pk]))

    assert response.status_code == 302
    assert response.url.endswith("#solution-generation-quality")
    repair_service.assert_not_called()
