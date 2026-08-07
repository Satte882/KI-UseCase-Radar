from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from ki_radar.architecture.forms import SolutionOptionForm
from ki_radar.architecture.models import ProcessAnalysis, SolutionOption
from ki_radar.architecture.permissions import can_edit_value_stream

from .models import SolutionGenerationRun
from .solution_generation_contract import GENERATED_OPTION_FIELDS, OPTION_LANES
from .solution_generation_sources import build_solution_generation_source_context
from .solution_generation_validation import (
    SolutionGenerationContractError,
    validate_solution_generation_payload,
)

LANE_OPTION_TYPES = {
    "organizational": SolutionOption.OptionType.ORGANIZATIONAL,
    "rule_automation": SolutionOption.OptionType.RULE_AUTOMATION,
    "assistant": SolutionOption.OptionType.ASSISTANT,
}


class SolutionGenerationAdoptionError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SolutionGenerationAdoptionResult:
    options: tuple[SolutionOption, ...]
    created: bool


def _normalize_selected_lanes(selected_lanes: tuple[str, ...] | None) -> tuple[str, ...]:
    if selected_lanes is None:
        return OPTION_LANES
    if not selected_lanes:
        raise SolutionGenerationAdoptionError(
            "Bitte mindestens einen KI-Entwurf für die Übernahme auswählen.",
            code="no_selection",
        )

    if len(set(selected_lanes)) != len(selected_lanes):
        raise SolutionGenerationAdoptionError(
            "Die Auswahl der KI-Entwürfe ist ungültig.",
            code="invalid_selection",
        )
    unknown_lanes = set(selected_lanes) - set(OPTION_LANES)
    if unknown_lanes:
        raise SolutionGenerationAdoptionError(
            "Die Auswahl enthält eine unbekannte Lösungsrichtung.",
            code="invalid_selection",
        )
    return tuple(lane for lane in OPTION_LANES if lane in selected_lanes)


def _normalized_edits(preview_payload: dict) -> dict[str, dict[str, str]]:
    edits = preview_payload.get("edits", {})
    if not isinstance(edits, dict):
        raise SolutionGenerationAdoptionError(
            "Die gespeicherten Bearbeitungen sind ungültig. Bitte neu generieren.",
            code="invalid_preview",
        )

    unknown_lanes = set(edits) - set(OPTION_LANES)
    if unknown_lanes:
        raise SolutionGenerationAdoptionError(
            "Die gespeicherten Bearbeitungen enthalten eine unbekannte Lösungsrichtung.",
            code="invalid_preview",
        )

    normalized: dict[str, dict[str, str]] = {}
    for lane, lane_edits in edits.items():
        if not isinstance(lane_edits, dict):
            raise SolutionGenerationAdoptionError(
                "Die gespeicherten Bearbeitungen sind ungültig. Bitte neu generieren.",
                code="invalid_preview",
            )
        unknown_fields = set(lane_edits) - set(GENERATED_OPTION_FIELDS)
        if unknown_fields:
            raise SolutionGenerationAdoptionError(
                "Die gespeicherten Bearbeitungen enthalten ein nicht freigegebenes Feld.",
                code="invalid_preview",
            )
        normalized_lane: dict[str, str] = {}
        for field_name, value in lane_edits.items():
            if not isinstance(value, str) or not value.strip():
                raise SolutionGenerationAdoptionError(
                    "Bearbeitete Entwurfsfelder dürfen nicht leer sein.",
                    code="invalid_preview",
                )
            normalized_lane[field_name] = value.strip()
        if normalized_lane:
            normalized[lane] = normalized_lane
    return normalized


def _validated_effective_payload(preview_payload: dict, source_context) -> dict:
    raw_payload = {
        "schema_version": preview_payload.get("schema_version"),
        "prompt_version": preview_payload.get("prompt_version"),
        "options": preview_payload.get("options"),
    }
    try:
        validated = validate_solution_generation_payload(raw_payload, source_context)
    except SolutionGenerationContractError as exc:
        raise SolutionGenerationAdoptionError(
            "Die gespeicherte KI-Vorschau ist nicht mehr vertragskonform. Bitte neu generieren.",
            code="invalid_preview",
        ) from exc

    for lane, lane_edits in _normalized_edits(preview_payload).items():
        for field_name, value in lane_edits.items():
            validated["options"][lane][field_name]["text"] = value

    try:
        return validate_solution_generation_payload(validated, source_context)
    except SolutionGenerationContractError as exc:
        raise SolutionGenerationAdoptionError(
            "Eine Bearbeitung verletzt die Quellen- oder Inhaltsregeln. Bitte den Entwurf prüfen.",
            code="invalid_preview_edit",
        ) from exc


def _option_form_data(lane: str, option: dict) -> dict[str, str]:
    data = {field_name: option[field_name]["text"] for field_name in GENERATED_OPTION_FIELDS}
    data.update(
        {
            "option_type": LANE_OPTION_TYPES[lane],
            "evaluation_status": SolutionOption.EvaluationStatus.DRAFT,
            "feasibility": SolutionOption.Effort.NOT_ASSESSED,
            "integration_effort": SolutionOption.Effort.NOT_ASSESSED,
        }
    )
    return data


def _existing_adoption(
    *,
    run: SolutionGenerationRun,
    process_analysis: ProcessAnalysis,
) -> SolutionGenerationAdoptionResult | None:
    adoption = run.preview_payload.get("adoption")
    if adoption is None:
        return None
    if not isinstance(adoption, dict) or adoption.get("status") != "adopted":
        raise SolutionGenerationAdoptionError(
            "Der Übernahmestatus dieser Vorschau ist inkonsistent.",
            code="invalid_adoption_state",
        )

    option_ids = adoption.get("option_ids", [])
    if not isinstance(option_ids, list):
        raise SolutionGenerationAdoptionError(
            "Der Übernahmenachweis dieser Vorschau ist unvollständig.",
            code="invalid_adoption_state",
        )

    adopted_lanes = adoption.get("lanes")
    if adopted_lanes is None:
        if len(option_ids) != len(OPTION_LANES):
            raise SolutionGenerationAdoptionError(
                "Der Übernahmenachweis dieser Vorschau ist unvollständig.",
                code="invalid_adoption_state",
            )
        normalized_lanes = OPTION_LANES
    else:
        if not isinstance(adopted_lanes, list):
            raise SolutionGenerationAdoptionError(
                "Der Übernahmenachweis dieser Vorschau ist unvollständig.",
                code="invalid_adoption_state",
            )
        try:
            normalized_lanes = _normalize_selected_lanes(tuple(adopted_lanes))
        except SolutionGenerationAdoptionError as exc:
            raise SolutionGenerationAdoptionError(
                "Der Übernahmenachweis dieser Vorschau ist unvollständig.",
                code="invalid_adoption_state",
            ) from exc

    if len(option_ids) != len(normalized_lanes):
        raise SolutionGenerationAdoptionError(
            "Der Übernahmenachweis dieser Vorschau ist unvollständig.",
            code="invalid_adoption_state",
        )

    options_by_id = {
        str(option.pk): option
        for option in SolutionOption.objects.filter(
            process_analysis=process_analysis,
            pk__in=option_ids,
        )
    }
    if len(options_by_id) != len(normalized_lanes):
        raise SolutionGenerationAdoptionError(
            "Die bereits übernommenen Lösungsoptionen sind nicht vollständig vorhanden.",
            code="invalid_adoption_state",
        )

    ordered = tuple(options_by_id[str(option_id)] for option_id in option_ids)
    if any(
        option.option_type != LANE_OPTION_TYPES[lane]
        for lane, option in zip(normalized_lanes, ordered, strict=True)
    ):
        raise SolutionGenerationAdoptionError(
            "Der Übernahmenachweis dieser Vorschau ist inkonsistent.",
            code="invalid_adoption_state",
        )
    return SolutionGenerationAdoptionResult(options=ordered, created=False)


@transaction.atomic
def adopt_solution_generation_bundle(
    *,
    actor,
    run_id,
    selected_lanes: tuple[str, ...] | None = None,
) -> SolutionGenerationAdoptionResult:
    run_reference = SolutionGenerationRun.objects.only("process_analysis_id").get(pk=run_id)
    process_analysis = (
        ProcessAnalysis.objects.select_for_update()
        .prefetch_related("validations")
        .get(pk=run_reference.process_analysis_id)
    )
    run = SolutionGenerationRun.objects.select_for_update().get(
        pk=run_id,
        process_analysis=process_analysis,
    )

    if not can_edit_value_stream(actor, process_analysis.stage.value_stream):
        raise PermissionDenied

    existing = _existing_adoption(run=run, process_analysis=process_analysis)
    if existing is not None:
        return existing

    normalized_lanes = _normalize_selected_lanes(selected_lanes)

    if run.status != SolutionGenerationRun.Status.SUCCESS or not run.preview_payload:
        raise SolutionGenerationAdoptionError(
            "Diese KI-Vorschau kann nicht übernommen werden.",
            code="preview_unavailable",
        )
    if run.expires_at <= timezone.now():
        raise SolutionGenerationAdoptionError(
            "Diese KI-Vorschau ist abgelaufen. Bitte neu generieren.",
            code="preview_expired",
        )

    source_context = build_solution_generation_source_context(process_analysis)
    if (
        source_context.source_hash != run.source_hash
        or source_context.process_version != run.process_version
        or not source_context.is_ready
    ):
        raise SolutionGenerationAdoptionError(
            "Die Prozessdaten haben sich geändert. Bitte die Entwürfe neu generieren.",
            code="preview_stale",
        )

    effective_payload = _validated_effective_payload(run.preview_payload, source_context)
    forms: list[SolutionOptionForm] = []
    form_errors: list[str] = []
    for lane in normalized_lanes:
        form = SolutionOptionForm(
            _option_form_data(lane, effective_payload["options"][lane]),
            process_analysis=process_analysis,
        )
        forms.append(form)
        if not form.is_valid():
            form_errors.append(lane)

    if form_errors:
        raise SolutionGenerationAdoptionError(
            "Mindestens ein ausgewählter Entwurf erfüllt den regulären Lösungsoptionsvertrag nicht.",
            code="option_form_invalid",
        )

    created_options: list[SolutionOption] = []
    for form in forms:
        option = form.save(commit=False)
        option.process_analysis = process_analysis
        option.created_by = actor
        option.recommendation = SolutionOption.Recommendation.CANDIDATE
        option.evaluation_status = SolutionOption.EvaluationStatus.DRAFT
        option.feasibility = SolutionOption.Effort.NOT_ASSESSED
        option.integration_effort = SolutionOption.Effort.NOT_ASSESSED
        option.full_clean()
        option.save()
        created_options.append(option)

    preview_payload = dict(run.preview_payload)
    preview_payload["adoption"] = {
        "status": "adopted",
        "lanes": list(normalized_lanes),
        "option_ids": [str(option.pk) for option in created_options],
        "adopted_at": timezone.now().isoformat(),
        "actor_id": actor.pk,
    }
    run.preview_payload = preview_payload
    run.save(update_fields=["preview_payload", "updated_at"])

    return SolutionGenerationAdoptionResult(options=tuple(created_options), created=True)
