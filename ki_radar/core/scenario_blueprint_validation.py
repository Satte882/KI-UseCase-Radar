from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ki_radar.accounts.models import BusinessUnit, User
from ki_radar.architecture.forms import (
    ProcessAnalysisForm,
    SolutionOptionForm,
    ValueStreamForm,
    ValueStreamStageForm,
    is_eligible_value_stream_owner,
)
from ki_radar.use_cases.forms import UseCaseForm

from .scenario_blueprint import blueprint_checksum, load_blueprint_json

CONTRACT_PATH = Path(__file__).with_name("scenario_blueprints") / "contract.v1.json"


class BlueprintValidationError(ValueError):
    def __init__(self, errors: list[str] | tuple[str, ...]):
        self.errors = tuple(errors)
        super().__init__("Blueprint ungültig: " + " | ".join(self.errors))


@dataclass(frozen=True)
class ResolvedBlueprint:
    payload: dict[str, Any]
    checksum: str
    business_unit: BusinessUnit
    actors: dict[str, User]


def load_blueprint_contract() -> dict[str, Any]:
    return load_blueprint_json(CONTRACT_PATH)


def _mapping(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{path}: Objekt erwartet.")
    return {}


def _items(value: Any, path: str, errors: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{path}: Liste erwartet.")
    return []


def _check_fields(
    value: dict[str, Any],
    section: str,
    contract: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    allowed = set(contract["allowed_fields"][section])
    required = set(contract["required_fields"][section])
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        errors.append(f"{path}: Unbekannte Felder: {', '.join(unknown)}.")
    if missing:
        errors.append(f"{path}: Pflichtfelder fehlen: {', '.join(missing)}.")


def _check_text(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: Nichtleere Zeichenkette erwartet.")


def _check_state(
    payload: dict[str, Any],
    path: str,
    allowed_states: dict[str, list[str]],
    state_key: str,
    errors: list[str],
) -> None:
    value = payload.get(path.rsplit(".", 1)[-1])
    if value not in allowed_states[state_key]:
        allowed = ", ".join(allowed_states[state_key])
        errors.append(f"{path}: Nur {allowed} ist zulässig.")


def _check_enum(
    value: Any,
    path: str,
    allowed: list[str],
    errors: list[str],
) -> None:
    if value not in allowed:
        errors.append(f"{path}: Ungültiger Wert {value!r}.")


def _check_key(
    value: Any,
    path: str,
    pattern: re.Pattern[str],
    max_length: int,
    errors: list[str],
) -> None:
    if not isinstance(value, str) or len(value) > max_length or pattern.fullmatch(value) is None:
        errors.append(f"{path}: Ungültiger stabiler Schlüssel.")


def _form_errors(label: str, form) -> list[str]:
    result = []
    for field, messages in form.errors.get_json_data().items():
        for message in messages:
            result.append(f"{label}.{field}: {message['message']}")
    return result


def _validate_structure(
    payload: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    top_allowed = set(contract["required_top_level"])
    unknown_top = sorted(set(payload) - top_allowed)
    missing_top = sorted(top_allowed - set(payload))
    if unknown_top:
        errors.append(f"root: Unbekannte Felder: {', '.join(unknown_top)}.")
    if missing_top:
        errors.append(f"root: Pflichtfelder fehlen: {', '.join(missing_top)}.")
    if payload.get("schema_version") != contract["schema_version"]:
        errors.append(
            "schema_version: Nur Version "
            f"{contract['schema_version']} wird unterstützt."
        )

    pattern = re.compile(contract["keys"]["pattern"])
    max_length = int(contract["keys"]["max_length"])
    _check_key(payload.get("scenario_key"), "scenario_key", pattern, max_length, errors)
    _check_text(payload.get("scenario_name"), "scenario_name", errors)

    references = _mapping(payload.get("references"), "references", errors)
    _check_fields(references, "references", contract, "references", errors)
    business_unit_ref = _mapping(
        references.get("business_unit"),
        "references.business_unit",
        errors,
    )
    _check_fields(
        business_unit_ref,
        "references.business_unit",
        contract,
        "references.business_unit",
        errors,
    )
    _check_text(
        business_unit_ref.get("name"),
        "references.business_unit.name",
        errors,
    )
    actors = _mapping(references.get("actors"), "references.actors", errors)
    _check_fields(
        actors,
        "references.actors",
        contract,
        "references.actors",
        errors,
    )
    for actor_name, actor_ref in actors.items():
        actor = _mapping(actor_ref, f"references.actors.{actor_name}", errors)
        _check_fields(
            actor,
            "user_reference",
            contract,
            f"references.actors.{actor_name}",
            errors,
        )
        _check_text(
            actor.get("username"),
            f"references.actors.{actor_name}.username",
            errors,
        )

    value_stream = _mapping(payload.get("value_stream"), "value_stream", errors)
    _check_fields(value_stream, "value_stream", contract, "value_stream", errors)
    _check_key(value_stream.get("key"), "value_stream.key", pattern, max_length, errors)
    _check_state(
        value_stream,
        "value_stream.status",
        contract["allowed_states"],
        "value_stream.status",
        errors,
    )
    focus = _mapping(value_stream.get("focus"), "value_stream.focus", errors)
    _check_fields(focus, "value_stream.focus", contract, "value_stream.focus", errors)
    _check_state(
        focus,
        "value_stream.focus.status",
        contract["allowed_states"],
        "value_stream.focus.status",
        errors,
    )
    _check_enum(
        focus.get("business_domain"),
        "value_stream.focus.business_domain",
        contract["allowed_enums"]["business_domain"],
        errors,
    )
    stages = _items(value_stream.get("stages"), "value_stream.stages", errors)
    cardinality = contract["cardinality"]
    if not cardinality["stages_min"] <= len(stages) <= cardinality["stages_max"]:
        errors.append("value_stream.stages: Unzulässige Anzahl von Phasen.")
    stage_keys: set[str] = set()
    sequences: set[int] = set()
    for index, raw_stage in enumerate(stages):
        path = f"value_stream.stages[{index}]"
        stage = _mapping(raw_stage, path, errors)
        _check_fields(stage, "value_stream.stage", contract, path, errors)
        key = stage.get("key")
        _check_key(key, f"{path}.key", pattern, max_length, errors)
        if isinstance(key, str):
            if key in stage_keys:
                errors.append(f"{path}.key: Schlüssel mehrfach vorhanden.")
            stage_keys.add(key)
        sequence = stage.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{path}.sequence: Positive Ganzzahl erwartet.")
        elif sequence in sequences:
            errors.append(f"{path}.sequence: Reihenfolge mehrfach vorhanden.")
        else:
            sequences.add(sequence)

    process = _mapping(payload.get("process_analysis"), "process_analysis", errors)
    _check_fields(process, "process_analysis", contract, "process_analysis", errors)
    _check_key(process.get("key"), "process_analysis.key", pattern, max_length, errors)
    _check_state(
        process,
        "process_analysis.status",
        contract["allowed_states"],
        "process_analysis.status",
        errors,
    )
    if process.get("stage_key") not in stage_keys:
        errors.append("process_analysis.stage_key: Unbekannte Phase.")

    options = _items(payload.get("solution_options"), "solution_options", errors)
    if not cardinality["solution_options_min"] <= len(options) <= cardinality[
        "solution_options_max"
    ]:
        errors.append("solution_options: Unzulässige Anzahl von Lösungsoptionen.")
    option_keys: set[str] = set()
    for index, raw_option in enumerate(options):
        path = f"solution_options[{index}]"
        option = _mapping(raw_option, path, errors)
        _check_fields(option, "solution_option", contract, path, errors)
        key = option.get("key")
        _check_key(key, f"{path}.key", pattern, max_length, errors)
        if isinstance(key, str):
            if key in option_keys:
                errors.append(f"{path}.key: Schlüssel mehrfach vorhanden.")
            option_keys.add(key)
        _check_state(
            option,
            f"{path}.recommendation",
            contract["allowed_states"],
            "solution_options[].recommendation",
            errors,
        )
        _check_state(
            option,
            f"{path}.evaluation_status",
            contract["allowed_states"],
            "solution_options[].evaluation_status",
            errors,
        )
        _check_enum(
            option.get("option_type"),
            f"{path}.option_type",
            contract["allowed_enums"]["solution_option.option_type"],
            errors,
        )
        _check_enum(
            option.get("feasibility"),
            f"{path}.feasibility",
            contract["allowed_enums"]["solution_option.feasibility"],
            errors,
        )
        _check_enum(
            option.get("integration_effort"),
            f"{path}.integration_effort",
            contract["allowed_enums"]["solution_option.integration_effort"],
            errors,
        )

    use_case = _mapping(payload.get("use_case"), "use_case", errors)
    _check_fields(use_case, "use_case", contract, "use_case", errors)
    _check_key(use_case.get("key"), "use_case.key", pattern, max_length, errors)
    _check_state(
        use_case,
        "use_case.status",
        contract["allowed_states"],
        "use_case.status",
        errors,
    )
    _check_state(
        use_case,
        "use_case.decision_status",
        contract["allowed_states"],
        "use_case.decision_status",
        errors,
    )
    for field, enum_name in (
        ("priority", "use_case.priority"),
        ("solution_type", "use_case.solution_type"),
        ("hosting_type", "use_case.hosting_type"),
        ("business_value", "level"),
        ("technical_feasibility", "level"),
        ("data_readiness", "level"),
        ("risk_complexity", "level"),
    ):
        _check_enum(
            use_case.get(field),
            f"use_case.{field}",
            contract["allowed_enums"][enum_name],
            errors,
        )
    metric = _mapping(use_case.get("metric"), "use_case.metric", errors)
    _check_fields(metric, "use_case.metric", contract, "use_case.metric", errors)
    _check_enum(
        metric.get("type"),
        "use_case.metric.type",
        contract["allowed_enums"]["use_case.metric.type"],
        errors,
    )
    _check_enum(
        metric.get("direction"),
        "use_case.metric.direction",
        contract["allowed_enums"]["use_case.metric.direction"],
        errors,
    )
    classification = _mapping(
        use_case.get("classification"),
        "use_case.classification",
        errors,
    )
    _check_fields(
        classification,
        "use_case.classification",
        contract,
        "use_case.classification",
        errors,
    )
    _check_enum(
        classification.get("business_domain"),
        "use_case.classification.business_domain",
        contract["allowed_enums"]["business_domain"],
        errors,
    )

    origin = _mapping(payload.get("origin"), "origin", errors)
    _check_fields(origin, "origin", contract, "origin", errors)
    if origin.get("stage_key") not in stage_keys:
        errors.append("origin.stage_key: Unbekannte Phase.")
    if origin.get("process_analysis_key") != process.get("key"):
        errors.append("origin.process_analysis_key: Unbekannte Prozessanalyse.")
    if origin.get("solution_option_key") not in option_keys:
        errors.append("origin.solution_option_key: Unbekannte Lösungsoption.")
    return errors


def _resolve_references(
    payload: dict[str, Any],
    errors: list[str],
) -> tuple[BusinessUnit | None, dict[str, User]]:
    references = payload.get("references", {})
    business_unit_name = references.get("business_unit", {}).get("name")
    business_units = BusinessUnit.objects.filter(name=business_unit_name)
    if business_units.count() != 1:
        errors.append(
            "references.business_unit.name: Organisationseinheit fehlt oder ist nicht eindeutig."
        )
        business_unit = None
    else:
        business_unit = business_units.first()
        if business_unit is not None and not business_unit.is_active:
            errors.append(
                "references.business_unit.name: Organisationseinheit ist inaktiv."
            )

    actors: dict[str, User] = {}
    for role, actor_ref in references.get("actors", {}).items():
        username = actor_ref.get("username") if isinstance(actor_ref, dict) else None
        users = User.objects.filter(username=username)
        if users.count() != 1:
            errors.append(
                f"references.actors.{role}.username: Benutzer fehlt oder ist nicht eindeutig."
            )
            continue
        user = users.first()
        if user is None or not user.is_active or user.is_anonymized:
            errors.append(
                f"references.actors.{role}.username: Benutzer ist inaktiv oder anonymisiert."
            )
            continue
        actors[role] = user
    owner = actors.get("value_stream_owner")
    if owner is not None and not is_eligible_value_stream_owner(owner):
        errors.append(
            "references.actors.value_stream_owner: Benutzer ist nicht als Value-Stream-Owner berechtigt."
        )
    return business_unit, actors


def _validate_forms(
    payload: dict[str, Any],
    business_unit: BusinessUnit,
    actors: dict[str, User],
) -> list[str]:
    errors: list[str] = []
    value_stream = payload["value_stream"]
    focus = value_stream["focus"]
    value_stream_form = ValueStreamForm(
        data={
            **{
                key: value_stream[key]
                for key in (
                    "name",
                    "status",
                    "description",
                    "trigger",
                    "outcome",
                    "scope_in",
                    "scope_out",
                    "strategic_objective",
                    "stakeholders",
                    "constraints",
                )
            },
            "business_unit": business_unit.pk,
            "owner": actors["value_stream_owner"].pk,
            "business_domain": focus["business_domain"],
            "capability": focus["capability"],
            "strategic_impact": "",
            "economic_potential": "",
            "pain_intensity": "",
            "data_accessibility": "",
            "change_effort": "",
            "focus_status": focus["status"],
            "focus_rationale": "",
        }
    )
    if not value_stream_form.is_valid():
        errors.extend(_form_errors("value_stream", value_stream_form))

    for index, stage in enumerate(value_stream["stages"]):
        form = ValueStreamStageForm(
            data={
                key: stage[key]
                for key in (
                    "sequence",
                    "name",
                    "description",
                    "actors",
                    "systems",
                    "documents",
                    "pain_points",
                    "baseline_metrics",
                )
            }
        )
        if not form.is_valid():
            errors.extend(_form_errors(f"value_stream.stages[{index}]", form))

    process = payload["process_analysis"]
    process_form = ProcessAnalysisForm(
        data={
            key: process[key]
            for key in (
                "name",
                "status",
                "scope_start",
                "scope_end",
                "trigger",
                "outcome",
                "current_flow",
                "roles",
                "systems",
                "data_objects",
                "business_rules",
                "handoffs",
                "bottlenecks",
                "exceptions",
                "baseline_metrics",
                "target_state_principles",
            )
        }
    )
    if not process_form.is_valid():
        errors.extend(_form_errors("process_analysis", process_form))

    for index, option in enumerate(payload["solution_options"]):
        form = SolutionOptionForm(
            data={
                key: option[key]
                for key in (
                    "name",
                    "option_type",
                    "evaluation_status",
                    "description",
                    "expected_value",
                    "bottleneck_coverage",
                    "feasibility",
                    "data_requirements",
                    "application_impact",
                    "integration_effort",
                    "integration_impact",
                    "technology_constraints",
                    "risks",
                    "architecture_fit",
                )
            }
        )
        if not form.is_valid():
            errors.extend(_form_errors(f"solution_options[{index}]", form))

    use_case = payload["use_case"]
    metric = use_case["metric"]
    classification = use_case["classification"]
    use_case_form = UseCaseForm(
        data={
            **{
                key: use_case[key]
                for key in (
                    "title",
                    "summary",
                    "problem_statement",
                    "affected_process",
                    "target_users",
                    "priority",
                    "solution_type",
                    "hosting_type",
                    "provider",
                    "product_name",
                    "model_name",
                    "source_systems",
                    "data_sources",
                    "interface_description",
                    "intended_users",
                    "intended_purpose",
                    "expected_benefit",
                    "benefit_category",
                    "one_time_cost",
                    "recurring_cost",
                    "business_value",
                    "technical_feasibility",
                    "data_readiness",
                    "risk_complexity",
                    "human_oversight",
                    "support_responsibility",
                )
            },
            "business_unit": business_unit.pk,
            "business_domain": classification["business_domain"],
            "business_capability": classification["capability"],
            "process_area": classification["process_area"],
            "business_owner": actors["business_owner"].pk,
            "coordinator": actors["coordinator"].pk,
            "technical_owner": actors["technical_owner"].pk,
            "metric_name": metric["name"],
            "metric_type": metric["type"],
            "metric_direction": metric["direction"],
            "metric_unit": metric["unit"],
            "metric_baseline": metric["baseline"],
            "metric_target": metric["target"],
            "metric_measurement_method": metric["measurement_method"],
        }
    )
    if not use_case_form.is_valid():
        errors.extend(_form_errors("use_case", use_case_form))
    return errors


def validate_blueprint(payload: dict[str, Any]) -> ResolvedBlueprint:
    contract = load_blueprint_contract()
    errors = _validate_structure(payload, contract)
    if errors:
        raise BlueprintValidationError(errors)
    business_unit, actors = _resolve_references(payload, errors)
    required_roles = contract["references"]["users"]["required_roles"]
    if business_unit is not None and len(actors) == len(required_roles):
        errors.extend(_validate_forms(payload, business_unit, actors))
    if errors or business_unit is None:
        raise BlueprintValidationError(errors)
    return ResolvedBlueprint(
        payload=payload,
        checksum=blueprint_checksum(payload),
        business_unit=business_unit,
        actors=actors,
    )
