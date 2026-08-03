from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import ProcessAnalysis, SolutionOption, UseCaseOrigin, ValueStreamStage

SCHEMA_VERSION = 1
COPY_MODE = "copy_on_create"

FIELD_LABELS = {
    "name": "Bezeichnung",
    "title": "Titel",
    "summary": "Kurzbeschreibung",
    "problem_statement": "Problem",
    "affected_process": "Betroffener Prozess",
    "target_users": "Zielgruppe",
    "source_systems": "Quellsysteme",
    "intended_users": "Vorgesehene Nutzer",
    "intended_purpose": "Vorgesehener Zweck",
    "expected_benefit": "Erwarteter Nutzen",
    "data_sources": "Datenquellen",
    "trigger": "Auslöser",
    "outcome": "Ergebnis",
    "roles": "Rollen und Verantwortlichkeiten",
    "systems": "Anwendungen und Arbeitsmittel",
    "data_objects": "Datenobjekte und Dokumente",
    "bottlenecks": "Bottlenecks und Ursachen",
    "baseline_metrics": "Baseline und Prozesskennzahlen",
}


def _entry(*, artifact_type: str, artifact_label: str, source, source_field: str, value: Any):
    return {
        "artifact_type": artifact_type,
        "artifact_label": artifact_label,
        "source_id": str(source.pk),
        "source_field": source_field,
        "source_value": value or "",
        "source_updated_at": source.updated_at.isoformat() if source.updated_at else "",
        "adoption": "copied",
    }


def _manifest(fields: dict[str, dict]) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "copy_mode": COPY_MODE,
        "fields": fields,
    }


def build_process_prefill(stage: ValueStreamStage) -> tuple[dict[str, Any], dict]:
    value_stream = stage.value_stream
    values: dict[str, Any] = {}
    fields: dict[str, dict] = {}

    def add(target: str, source, artifact_type: str, artifact_label: str, source_field: str):
        value = getattr(source, source_field)
        values[target] = value
        fields[target] = _entry(
            artifact_type=artifact_type,
            artifact_label=artifact_label,
            source=source,
            source_field=source_field,
            value=value,
        )

    add("name", stage, "value_stream_stage", "Value-Stream-Phase", "name")
    add("trigger", value_stream, "value_stream", "Value Stream", "trigger")
    if stage.description.strip():
        add("outcome", stage, "value_stream_stage", "Value-Stream-Phase", "description")
    else:
        add("outcome", value_stream, "value_stream", "Value Stream", "outcome")
    add("roles", stage, "value_stream_stage", "Value-Stream-Phase", "actors")
    add("systems", stage, "value_stream_stage", "Value-Stream-Phase", "systems")
    add("data_objects", stage, "value_stream_stage", "Value-Stream-Phase", "documents")
    add("bottlenecks", stage, "value_stream_stage", "Value-Stream-Phase", "pain_points")
    add(
        "baseline_metrics",
        stage,
        "value_stream_stage",
        "Value-Stream-Phase",
        "baseline_metrics",
    )
    return values, _manifest(fields)


def build_stage_use_case_prefill(stage: ValueStreamStage) -> tuple[dict[str, Any], dict]:
    mapping = {
        "title": (stage, "value_stream_stage", "Value-Stream-Phase", "name"),
        "affected_process": (stage, "value_stream_stage", "Value-Stream-Phase", "name"),
        "summary": (stage, "value_stream_stage", "Value-Stream-Phase", "description"),
        "target_users": (stage, "value_stream_stage", "Value-Stream-Phase", "actors"),
        "source_systems": (stage, "value_stream_stage", "Value-Stream-Phase", "systems"),
    }
    if stage.pain_points.strip():
        mapping["problem_statement"] = (
            stage,
            "value_stream_stage",
            "Value-Stream-Phase",
            "pain_points",
        )
    return _build_use_case_values(mapping)


def build_option_use_case_prefill(
    option: SolutionOption,
    *,
    solution_type: str,
) -> tuple[dict[str, Any], dict]:
    process = option.process_analysis
    stage = process.stage
    data_source = option if option.data_requirements.strip() else process
    data_source_field = "data_requirements" if data_source is option else "data_objects"
    data_artifact_type = "solution_option" if data_source is option else "process_analysis"
    data_artifact_label = "Lösungsoption" if data_source is option else "Prozessanalyse"
    mapping = {
        "title": (option, "solution_option", "Lösungsoption", "name"),
        "problem_statement": (
            process,
            "process_analysis",
            "Prozessanalyse",
            "bottlenecks",
        ),
        "affected_process": (process, "process_analysis", "Prozessanalyse", "name"),
        "summary": (process, "process_analysis", "Prozessanalyse", "current_flow"),
        "target_users": (process, "process_analysis", "Prozessanalyse", "roles"),
        "source_systems": (process, "process_analysis", "Prozessanalyse", "systems"),
        "intended_users": (process, "process_analysis", "Prozessanalyse", "roles"),
        "intended_purpose": (option, "solution_option", "Lösungsoption", "description"),
        "expected_benefit": (option, "solution_option", "Lösungsoption", "expected_value"),
        "data_sources": (
            data_source,
            data_artifact_type,
            data_artifact_label,
            data_source_field,
        ),
    }
    values, manifest = _build_use_case_values(mapping)
    values["solution_type"] = solution_type
    values["source_stage_id"] = str(stage.pk)
    values["source_process_analysis_id"] = str(process.pk)
    values["source_solution_option_id"] = str(option.pk)
    return values, manifest


def _build_use_case_values(mapping: Mapping[str, tuple]) -> tuple[dict[str, Any], dict]:
    values: dict[str, Any] = {}
    fields: dict[str, dict] = {}
    for target, (source, artifact_type, artifact_label, source_field) in mapping.items():
        value = getattr(source, source_field)
        values[target] = value
        fields[target] = _entry(
            artifact_type=artifact_type,
            artifact_label=artifact_label,
            source=source,
            source_field=source_field,
            value=value,
        )
    return values, _manifest(fields)


def _source_for_process(process: ProcessAnalysis, artifact_type: str):
    if artifact_type == "value_stream":
        return process.stage.value_stream
    if artifact_type == "value_stream_stage":
        return process.stage
    return None


def _source_for_origin(origin: UseCaseOrigin, artifact_type: str):
    if artifact_type == "value_stream":
        return origin.stage.value_stream
    if artifact_type == "value_stream_stage":
        return origin.stage
    if artifact_type == "process_analysis":
        return origin.process_analysis
    if artifact_type == "solution_option":
        return origin.solution_option
    return None


def provenance_rows(*, manifest: dict, working_object, source_resolver) -> list[dict]:
    rows = []
    for field_name, entry in (manifest.get("fields") or {}).items():
        source = source_resolver(entry.get("artifact_type", ""))
        current_source_value = ""
        if source is not None and entry.get("source_field"):
            current_source_value = getattr(source, entry["source_field"], "") or ""
        snapshot_value = entry.get("source_value", "") or ""
        working_value = getattr(working_object, field_name, "") or ""
        rows.append(
            {
                "field": field_name,
                "field_label": FIELD_LABELS.get(field_name, field_name.replace("_", " ").title()),
                "artifact_label": entry.get("artifact_label", "Quelle"),
                "source_field": entry.get("source_field", ""),
                "snapshot_value": snapshot_value,
                "current_source_value": current_source_value,
                "working_value": working_value,
                "source_changed": current_source_value != snapshot_value,
                "working_changed": working_value != snapshot_value,
            }
        )
    return rows


def process_provenance_rows(process: ProcessAnalysis) -> list[dict]:
    return provenance_rows(
        manifest=process.source_manifest,
        working_object=process,
        source_resolver=lambda artifact_type: _source_for_process(process, artifact_type),
    )


def use_case_provenance_rows(origin: UseCaseOrigin) -> list[dict]:
    return provenance_rows(
        manifest=origin.source_manifest,
        working_object=origin.use_case,
        source_resolver=lambda artifact_type: _source_for_origin(origin, artifact_type),
    )


def stored_provenance_rows(stored: dict) -> list[dict]:
    manifest = stored.get("_source_manifest") or {}
    rows = []
    for field_name, entry in (manifest.get("fields") or {}).items():
        rows.append(
            {
                "field": field_name,
                "field_label": FIELD_LABELS.get(field_name, field_name.replace("_", " ").title()),
                "artifact_label": entry.get("artifact_label", "Quelle"),
                "snapshot_value": entry.get("source_value", "") or "",
                "working_value": stored.get(field_name, "") or "",
            }
        )
    return rows
