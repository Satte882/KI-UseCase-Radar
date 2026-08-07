from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import SolutionGenerationRun
from .solution_generation_contract import GENERATED_OPTION_FIELDS, OPTION_LANES
from .solution_generation_sources import build_solution_generation_source_context


class SolutionGenerationPreviewError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SolutionGenerationPreviewState:
    stale: bool
    expired: bool
    current_ready: bool
    validation_state: str

    @property
    def editable(self) -> bool:
        return not self.stale and not self.expired and self.current_ready


def build_solution_generation_preview_state(
    run: SolutionGenerationRun,
) -> SolutionGenerationPreviewState:
    current_context = build_solution_generation_source_context(run.process_analysis)
    stale = (
        current_context.source_hash != run.source_hash
        or current_context.process_version != run.process_version
    )
    return SolutionGenerationPreviewState(
        stale=stale,
        expired=run.expires_at <= timezone.now(),
        current_ready=current_context.is_ready,
        validation_state=current_context.validation_state,
    )


def _normalize_edits(
    preview_payload: dict,
    edits: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    options = preview_payload.get("options", {})
    unknown_lanes = set(edits) - set(OPTION_LANES)
    if unknown_lanes:
        raise SolutionGenerationPreviewError(
            "Die Bearbeitung enthält eine unbekannte Lösungsrichtung.",
            code="invalid_preview_edit",
        )

    normalized: dict[str, dict[str, str]] = {}
    for lane, lane_edits in edits.items():
        unknown_fields = set(lane_edits) - set(GENERATED_OPTION_FIELDS)
        if unknown_fields:
            raise SolutionGenerationPreviewError(
                "Die Bearbeitung enthält ein nicht freigegebenes Entwurfsfeld.",
                code="invalid_preview_edit",
            )
        normalized_lane: dict[str, str] = {}
        for field_name, value in lane_edits.items():
            text = str(value).strip()
            if not text:
                raise SolutionGenerationPreviewError(
                    "Entwurfsfelder dürfen nicht leer gespeichert werden.",
                    code="invalid_preview_edit",
                )
            original = str(options[lane][field_name]["text"]).strip()
            if text != original:
                normalized_lane[field_name] = text
        if normalized_lane:
            normalized[lane] = normalized_lane
    return normalized


@transaction.atomic
def update_solution_generation_preview_edits(
    *,
    run_id,
    edits: dict[str, dict[str, str]],
) -> SolutionGenerationRun:
    run = (
        SolutionGenerationRun.objects.select_for_update()
        .select_related("process_analysis__stage__value_stream")
        .prefetch_related("process_analysis__validations")
        .get(pk=run_id)
    )
    if run.status != SolutionGenerationRun.Status.SUCCESS or not run.preview_payload:
        raise SolutionGenerationPreviewError(
            "Diese KI-Vorschau ist nicht zur Bearbeitung verfügbar.",
            code="preview_unavailable",
        )

    state = build_solution_generation_preview_state(run)
    if state.expired:
        raise SolutionGenerationPreviewError(
            "Diese KI-Vorschau ist abgelaufen. Bitte neu generieren.",
            code="preview_expired",
        )
    if state.stale or not state.current_ready:
        raise SolutionGenerationPreviewError(
            "Die Prozessdaten haben sich geändert. Bitte die Entwürfe neu generieren.",
            code="preview_stale",
        )

    preview_payload = dict(run.preview_payload)
    preview_payload["edits"] = _normalize_edits(preview_payload, edits)
    run.preview_payload = preview_payload
    run.save(update_fields=["preview_payload", "updated_at"])
    return run
