from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ki_radar.architecture.models import ProcessAnalysis
from ki_radar.architecture.permissions import can_edit_value_stream

from .models import SolutionGenerationRun
from .solution_generation_adoption import (
    SolutionGenerationAdoptionError,
    adopt_solution_generation_bundle,
)
from .solution_generation_contract import GENERATED_OPTION_FIELDS, OPTION_LANES
from .solution_generation_forms import (
    FIELD_LABELS,
    LANE_LABELS,
    SOURCE_LABELS,
    UNCERTAINTY_LABELS,
    VALIDATION_LABELS,
    SolutionGenerationPreviewEditForm,
    preview_form_field_name,
)
from .solution_generation_preview import (
    SolutionGenerationPreviewError,
    build_solution_generation_preview_state,
    update_solution_generation_preview_edits,
)
from .solution_generation_service import SolutionGenerationError, generate_solution_preview


def _generation_error_message(exc: SolutionGenerationError) -> str:
    if exc.code in {
        "context_quota_exceeded",
        "user_quota_exceeded",
        "global_quota_exceeded",
        "generation_already_running",
        "generation_superseded",
        "process_not_ready",
        "input_too_large",
        "invalid_configuration",
        "invalid_generation_payload",
        "internal_error",
        "not_configured",
        "unauthorized",
        "provider_schema_unsupported",
        "provider_unavailable",
        "provider_error",
        "invalid_response",
        "empty_response",
        "response_too_large",
        "unavailable",
    }:
        return str(exc)
    if exc.code == "rate_limit":
        return (
            "Der KI-Dienst hat sein aktuelles Anfrage-Limit erreicht. "
            "Bestehende Prozessdaten und Lösungsoptionen bleiben unverändert."
        )
    if exc.code == "timeout":
        return (
            "Die KI-Generierung hat das Zeitlimit überschritten. "
            "Es wurden keine Lösungsoptionen angelegt."
        )
    if exc.code == "output_truncated":
        return (
            "Die KI-Antwort war unvollständig und wurde verworfen. "
            "Es wurden keine Lösungsoptionen angelegt."
        )
    return (
        "Die KI-Generierung ist derzeit nicht verfügbar. Es wurden keine Lösungsoptionen angelegt."
    )


def _process_queryset():
    return ProcessAnalysis.objects.select_related(
        "stage__value_stream__owner",
    ).prefetch_related("validations")


def _run_queryset():
    return SolutionGenerationRun.objects.select_related(
        "process_analysis__stage__value_stream__owner",
    ).prefetch_related("process_analysis__validations")


@login_required
@require_POST
def solution_generation_start(request, process_pk):
    process_analysis = get_object_or_404(_process_queryset(), pk=process_pk)
    if not can_edit_value_stream(request.user, process_analysis.stage.value_stream):
        raise PermissionDenied

    try:
        run = generate_solution_preview(
            actor=request.user,
            process_analysis_id=process_analysis.pk,
        )
    except SolutionGenerationError as exc:
        messages.error(
            request,
            _generation_error_message(exc),
            extra_tags="solution-generation-feedback",
        )
        return HttpResponseRedirect(f"{process_analysis.get_absolute_url()}#loesungsoptionen")

    preview_url = reverse("accelerator:solution_generation_preview", kwargs={"run_id": run.pk})
    return HttpResponseRedirect(f"{preview_url}#solution-generation-result")


@login_required
@require_POST
def solution_generation_adopt(request, run_id):
    run = get_object_or_404(
        _run_queryset(),
        pk=run_id,
        status=SolutionGenerationRun.Status.SUCCESS,
    )
    process_analysis = run.process_analysis
    if not can_edit_value_stream(request.user, process_analysis.stage.value_stream):
        raise PermissionDenied

    try:
        result = adopt_solution_generation_bundle(actor=request.user, run_id=run.pk)
    except SolutionGenerationAdoptionError as exc:
        messages.error(request, str(exc))
        return redirect("accelerator:solution_generation_preview", run_id=run.pk)

    if result.created:
        messages.success(
            request,
            "Drei KI-Entwürfe wurden als reguläre, noch nicht bewertete "
            "Lösungsoptionen übernommen.",
        )
    else:
        messages.info(
            request,
            "Diese drei KI-Entwürfe waren bereits vollständig übernommen.",
        )
    return redirect("architecture:solution_option_compare", pk=process_analysis.pk)


def _preview_source_facts(preview_payload: dict) -> list[dict[str, str]]:
    facts = preview_payload.get("source_context", {}).get("facts", [])
    return [
        {
            "source_id": fact["source_id"],
            "label": SOURCE_LABELS.get(fact["source_id"], fact["source_id"]),
            "value": fact["value"],
        }
        for fact in facts
    ]


def _preview_options(preview_payload: dict, form) -> list[dict[str, object]]:
    options = preview_payload.get("options", {})
    edits = preview_payload.get("edits", {})
    result: list[dict[str, object]] = []

    for lane in OPTION_LANES:
        lane_edits = edits.get(lane, {})
        fields: list[dict[str, object]] = []
        for field_name in GENERATED_OPTION_FIELDS:
            statement = options[lane][field_name]
            key = preview_form_field_name(lane, field_name)
            source_ids = statement.get("source_ids", [])
            uncertainty = statement.get("uncertainty", {})
            fields.append(
                {
                    "name": field_name,
                    "label": FIELD_LABELS[field_name],
                    "text": lane_edits.get(field_name, statement["text"]),
                    "edited": field_name in lane_edits,
                    "form_field": form[key] if form is not None else None,
                    "sources": [
                        {
                            "source_id": source_id,
                            "label": SOURCE_LABELS.get(source_id, source_id),
                        }
                        for source_id in source_ids
                    ],
                    "assumptions": statement.get("assumptions", []),
                    "open_evidence": statement.get("open_evidence", []),
                    "uncertainty_label": UNCERTAINTY_LABELS.get(
                        uncertainty.get("level", ""),
                        uncertainty.get("level", ""),
                    ),
                    "uncertainty_reason": uncertainty.get("reason", ""),
                }
            )
        result.append(
            {
                "lane": lane,
                "label": LANE_LABELS[lane],
                "fields": fields,
            }
        )
    return result


@login_required
def solution_generation_preview(request, run_id):
    run = get_object_or_404(
        _run_queryset(),
        pk=run_id,
        status=SolutionGenerationRun.Status.SUCCESS,
    )
    process_analysis = run.process_analysis
    value_stream = process_analysis.stage.value_stream
    can_edit = can_edit_value_stream(request.user, value_stream)
    state = build_solution_generation_preview_state(run)
    editable = can_edit and state.editable

    form = SolutionGenerationPreviewEditForm(
        request.POST or None,
        preview_payload=run.preview_payload,
    )
    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied
        if not state.editable:
            messages.warning(
                request,
                "Diese Vorschau ist nicht mehr bearbeitbar. Bitte neu generieren.",
            )
            return redirect("accelerator:solution_generation_preview", run_id=run.pk)
        if form.is_valid():
            try:
                update_solution_generation_preview_edits(
                    run_id=run.pk,
                    edits=form.normalized_edits(run.preview_payload),
                )
            except SolutionGenerationPreviewError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    "Die Bearbeitungen am KI-Entwurf wurden gespeichert.",
                )
            return redirect("accelerator:solution_generation_preview", run_id=run.pk)

    source_context = run.preview_payload.get("source_context", {})
    frozen_validation_state = source_context.get("validation_state", "")
    return render(
        request,
        "accelerator/solution_generation_preview.html",
        {
            "run": run,
            "process_analysis": process_analysis,
            "state": state,
            "editable": editable,
            "form": form,
            "preview_options": _preview_options(
                run.preview_payload,
                form if editable else None,
            ),
            "source_facts": _preview_source_facts(run.preview_payload),
            "frozen_validation_label": VALIDATION_LABELS.get(
                frozen_validation_state,
                frozen_validation_state,
            ),
            "current_validation_label": VALIDATION_LABELS.get(
                state.validation_state,
                state.validation_state,
            ),
        },
    )
