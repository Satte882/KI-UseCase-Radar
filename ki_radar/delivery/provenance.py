from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist

from .models import DeliveryPackage

SCHEMA_VERSION = 2
COPY_MODE = "copy_on_create"

FIELD_LABELS = {
    "problem_context": "Problem und Geschäftskontext",
    "target_outcome": "Ziel und erwartetes Ergebnis",
    "in_scope": "Im Scope",
    "out_of_scope": "Nicht im Scope",
    "users_and_scenarios": "Nutzer und Nutzungsszenarien",
    "solution_outline": "Lösungsrahmen und Zielbild",
    "system_context": "System- und Anwendungskontext",
    "data_context": "Datenobjekte und Datenquellen",
    "integrations": "Schnittstellen und Integrationen",
    "human_oversight": "Menschliche Aufsicht",
    "operations_and_support": "Betrieb und Support",
    "risks": "Risiken",
}

SECTION_FIELDS = {
    "problem_and_target": {"problem_context", "target_outcome"},
    "scope_and_users": {"in_scope", "out_of_scope", "users_and_scenarios"},
    "solution_direction": {"solution_outline"},
    "architecture_and_data": {"system_context", "data_context", "integrations"},
    "requirements_and_governance": {"human_oversight", "operations_and_support"},
    "acceptance_and_measurement": set(),
    "delivery_control": {"risks"},
}


def _entry(source, *, artifact_type: str, artifact_label: str, source_field: str, value):
    return {
        "artifact_type": artifact_type,
        "artifact_label": artifact_label,
        "source_id": str(source.pk),
        "source_field": source_field,
        "source_value": value or "",
        "source_updated_at": source.updated_at.isoformat() if source.updated_at else "",
        "adoption": "copied",
    }


def _origin(use_case):
    try:
        return use_case.architecture_origin
    except ObjectDoesNotExist:
        return None


def build_delivery_provenance(use_case) -> dict:
    origin = _origin(use_case)
    process = origin.process_analysis if origin else None
    option = origin.solution_option if origin else None
    value_stream = origin.stage.value_stream if origin else None
    fields = {}

    def add(target, source, artifact_type, artifact_label, source_field):
        if source is None:
            return
        fields[target] = _entry(
            source,
            artifact_type=artifact_type,
            artifact_label=artifact_label,
            source_field=source_field,
            value=getattr(source, source_field),
        )

    add("problem_context", use_case, "use_case", "Use Case", "problem_statement")
    add("target_outcome", use_case, "use_case", "Use Case", "expected_benefit")
    if value_stream:
        add("in_scope", value_stream, "value_stream", "Value Stream", "scope_in")
        add("out_of_scope", value_stream, "value_stream", "Value Stream", "scope_out")
    else:
        source_field = "summary" if use_case.summary else "affected_process"
        add("in_scope", use_case, "use_case", "Use Case", source_field)
    if process:
        add("users_and_scenarios", process, "process_analysis", "Prozessanalyse", "roles")
        add("system_context", process, "process_analysis", "Prozessanalyse", "systems")
    else:
        user_field = "intended_users" if use_case.intended_users else "target_users"
        add("users_and_scenarios", use_case, "use_case", "Use Case", user_field)
        add("system_context", use_case, "use_case", "Use Case", "source_systems")
    if option:
        add("solution_outline", option, "solution_option", "Lösungsoption", "description")
        if option.data_requirements:
            add("data_context", option, "solution_option", "Lösungsoption", "data_requirements")
        elif process:
            add("data_context", process, "process_analysis", "Prozessanalyse", "data_objects")
        else:
            add("data_context", use_case, "use_case", "Use Case", "data_sources")
        if option.integration_impact:
            add("integrations", option, "solution_option", "Lösungsoption", "integration_impact")
        else:
            add("integrations", use_case, "use_case", "Use Case", "interface_description")
        if option.risks:
            add("risks", option, "solution_option", "Lösungsoption", "risks")
    else:
        purpose_field = "intended_purpose" if use_case.intended_purpose else "summary"
        add("solution_outline", use_case, "use_case", "Use Case", purpose_field)
        if process:
            add("data_context", process, "process_analysis", "Prozessanalyse", "data_objects")
        else:
            add("data_context", use_case, "use_case", "Use Case", "data_sources")
        add("integrations", use_case, "use_case", "Use Case", "interface_description")
    if use_case.human_oversight:
        add("human_oversight", use_case, "use_case", "Use Case", "human_oversight")
    if use_case.support_responsibility:
        add(
            "operations_and_support",
            use_case,
            "use_case",
            "Use Case",
            "support_responsibility",
        )
    return {"schema_version": SCHEMA_VERSION, "copy_mode": COPY_MODE, "fields": fields}


def section_source_manifest(manifest: dict, section_key: str) -> dict:
    selected = {
        field: entry
        for field, entry in (manifest.get("fields") or {}).items()
        if field in SECTION_FIELDS[section_key]
    }
    return {
        "schema_version": manifest.get("schema_version", SCHEMA_VERSION),
        "copy_mode": manifest.get("copy_mode", COPY_MODE),
        "fields": selected,
        "section": section_key,
    }


def _resolve_source(package: DeliveryPackage, artifact_type: str):
    if artifact_type == "use_case":
        return package.use_case
    try:
        origin = package.use_case.architecture_origin
    except ObjectDoesNotExist:
        return None
    if artifact_type == "value_stream":
        return origin.stage.value_stream
    if artifact_type == "process_analysis":
        return origin.process_analysis
    if artifact_type == "solution_option":
        return origin.solution_option
    return None


def delivery_provenance_rows(package: DeliveryPackage, manifest: dict) -> list[dict]:
    rows = []
    for field_name, entry in (manifest.get("fields") or {}).items():
        source = _resolve_source(package, entry.get("artifact_type", ""))
        current = ""
        if source is not None:
            current = getattr(source, entry.get("source_field", ""), "") or ""
        snapshot = entry.get("source_value", "") or ""
        working = getattr(package, field_name, "") or ""
        rows.append(
            {
                "field": field_name,
                "field_label": FIELD_LABELS.get(field_name, field_name),
                "artifact_label": entry.get("artifact_label", "Quelle"),
                "snapshot_value": snapshot,
                "current_source_value": current,
                "working_value": working,
                "source_changed": current != snapshot,
                "working_changed": working != snapshot,
            }
        )
    return rows
