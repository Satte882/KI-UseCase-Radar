from __future__ import annotations

from typing import Any

from .solution_generation_contract import GENERATED_OPTION_FIELDS, OPTION_LANES
from .solution_generation_sources import SolutionGenerationSourceContext
from .solution_generation_validation import (
    SolutionGenerationContractError,
    validate_solution_generation_payload,
)


class SolutionGenerationEffectivePayloadError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def normalize_solution_generation_edits(
    preview_payload: dict[str, Any],
) -> dict[str, dict[str, str]]:
    edits = preview_payload.get("edits", {})
    if not isinstance(edits, dict):
        raise SolutionGenerationEffectivePayloadError(
            "Die gespeicherten Bearbeitungen sind ungültig. Bitte neu generieren.",
            code="invalid_preview",
        )

    unknown_lanes = set(edits) - set(OPTION_LANES)
    if unknown_lanes:
        raise SolutionGenerationEffectivePayloadError(
            "Die gespeicherten Bearbeitungen enthalten eine unbekannte Lösungsrichtung.",
            code="invalid_preview",
        )

    normalized: dict[str, dict[str, str]] = {}
    for lane, lane_edits in edits.items():
        if not isinstance(lane_edits, dict):
            raise SolutionGenerationEffectivePayloadError(
                "Die gespeicherten Bearbeitungen sind ungültig. Bitte neu generieren.",
                code="invalid_preview",
            )
        unknown_fields = set(lane_edits) - set(GENERATED_OPTION_FIELDS)
        if unknown_fields:
            raise SolutionGenerationEffectivePayloadError(
                "Die gespeicherten Bearbeitungen enthalten ein nicht freigegebenes Feld.",
                code="invalid_preview",
            )

        normalized_lane: dict[str, str] = {}
        for field_name, value in lane_edits.items():
            if not isinstance(value, str) or not value.strip():
                raise SolutionGenerationEffectivePayloadError(
                    "Bearbeitete Entwurfsfelder dürfen nicht leer sein.",
                    code="invalid_preview",
                )
            normalized_lane[field_name] = value.strip()
        if normalized_lane:
            normalized[lane] = normalized_lane
    return normalized


def build_validated_effective_solution_payload(
    preview_payload: dict[str, Any],
    source_context: SolutionGenerationSourceContext,
) -> dict[str, Any]:
    """Build the single canonical, deterministically valid Block-7 preview payload.

    The persisted generator output remains immutable. Human edits are applied as
    a text-only overlay and the complete result is validated again with the
    authoritative Block-7 validator. Later #212 steps extend this same contract
    with a validated machine-repair overlay rather than introducing a second
    interpretation of preview state.
    """

    raw_payload = {
        "schema_version": preview_payload.get("schema_version"),
        "prompt_version": preview_payload.get("prompt_version"),
        "options": preview_payload.get("options"),
    }
    try:
        validated = validate_solution_generation_payload(raw_payload, source_context)
    except SolutionGenerationContractError as exc:
        raise SolutionGenerationEffectivePayloadError(
            "Die gespeicherte KI-Vorschau ist nicht mehr vertragskonform. Bitte neu generieren.",
            code="invalid_preview",
        ) from exc

    for lane, lane_edits in normalize_solution_generation_edits(preview_payload).items():
        for field_name, value in lane_edits.items():
            validated["options"][lane][field_name]["text"] = value

    try:
        return validate_solution_generation_payload(validated, source_context)
    except SolutionGenerationContractError as exc:
        raise SolutionGenerationEffectivePayloadError(
            "Eine Bearbeitung verletzt die Quellen- oder Inhaltsregeln. Bitte den Entwurf prüfen.",
            code="invalid_preview_edit",
        ) from exc
