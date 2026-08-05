from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from django.core.exceptions import ObjectDoesNotExist

from ki_radar.architecture.focus import get_value_stream_focus
from ki_radar.architecture.models import (
    ProcessAnalysis,
    ProcessValidation,
    SolutionOption,
    SolutionSelectionDecision,
    UseCaseOrigin,
    ValueStream,
    ValueStreamStage,
)
from ki_radar.delivery.models import DeliveryPackage
from ki_radar.governance.models import GovernanceAssessment
from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase

from .scenario_blueprint_validation import ResolvedBlueprint


class DiffStatus(StrEnum):
    CREATE = "CREATE"
    NO_CHANGE = "NO_CHANGE"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class FieldDifference:
    field: str
    current: Any
    expected: Any


@dataclass(frozen=True)
class ObjectDifference:
    object_type: str
    key: str
    status: DiffStatus
    differences: tuple[FieldDifference, ...] = ()


@dataclass(frozen=True)
class BlueprintGraphDiff:
    scenario_key: str
    schema_version: str
    checksum: str
    objects: tuple[ObjectDifference, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(item.status == DiffStatus.CONFLICT for item in self.objects)

    @property
    def is_create(self) -> bool:
        return bool(self.objects) and all(
            item.status == DiffStatus.CREATE for item in self.objects
        )

    @property
    def is_no_change(self) -> bool:
        return bool(self.objects) and all(
            item.status == DiffStatus.NO_CHANGE for item in self.objects
        )

    @property
    def can_apply(self) -> bool:
        return self.is_create and not self.has_conflicts

    @property
    def graph_status(self) -> DiffStatus:
        if self.has_conflicts:
            return DiffStatus.CONFLICT
        if self.is_no_change:
            return DiffStatus.NO_CHANGE
        if self.is_create:
            return DiffStatus.CREATE
        return DiffStatus.CONFLICT

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.update(
            {
                "graph_status": self.graph_status.value,
                "has_conflicts": self.has_conflicts,
                "can_apply": self.can_apply,
                "dry_run": True,
                "data_changed": False,
            }
        )
        for item in result["objects"]:
            item["status"] = item["status"].value
        return result


def _display(value: Any) -> Any:
    if hasattr(value, "pk"):
        return str(value.pk)
    return value


def _field_differences(
    current: dict[str, Any], expected: dict[str, Any]
) -> tuple[FieldDifference, ...]:
    result = []
    for field in sorted(expected):
        current_value = current.get(field)
        expected_value = expected[field]
        if current_value != expected_value:
            result.append(
                FieldDifference(
                    field=field,
                    current=_display(current_value),
                    expected=_display(expected_value),
                )
            )
    return tuple(result)


def _object_diff(
    object_type: str,
    key: str,
    instance: Any | None,
    current: dict[str, Any] | None,
    expected: dict[str, Any],
) -> ObjectDifference:
    if instance is None:
        return ObjectDifference(object_type, key, DiffStatus.CREATE)
    differences = _field_differences(current or {}, expected)
    status = DiffStatus.CONFLICT if differences else DiffStatus.NO_CHANGE
    return ObjectDifference(object_type, key, status, differences)


def _stream_values(stream: ValueStream) -> dict[str, Any]:
    return {
        "name": stream.name,
        "status": stream.status,
        "description": stream.description,
        "business_unit": stream.business_unit_id,
        "owner": stream.owner_id,
        "trigger": stream.trigger,
        "outcome": stream.outcome,
        "scope_in": stream.scope_in,
        "scope_out": stream.scope_out,
        "strategic_objective": stream.strategic_objective,
        "stakeholders": stream.stakeholders,
        "constraints": stream.constraints,
    }


def _expected_stream(resolved: ResolvedBlueprint) -> dict[str, Any]:
    data = resolved.payload["value_stream"]
    return {
        "name": data["name"],
        "status": data["status"],
        "description": data["description"],
        "business_unit": resolved.business_unit.pk,
        "owner": resolved.actors["value_stream_owner"].pk,
        "trigger": data["trigger"],
        "outcome": data["outcome"],
        "scope_in": data["scope_in"],
        "scope_out": data["scope_out"],
        "strategic_objective": data["strategic_objective"],
        "stakeholders": data["stakeholders"],
        "constraints": data["constraints"],
    }


def _focus_diff(
    stream: ValueStream | None, resolved: ResolvedBlueprint
) -> ObjectDifference:
    expected = resolved.payload["value_stream"]["focus"]
    if stream is None:
        return ObjectDifference("value_stream_focus", "focus", DiffStatus.CREATE)
    focus = get_value_stream_focus(stream)
    if focus is None:
        return ObjectDifference("value_stream_focus", "focus", DiffStatus.CONFLICT)
    current = {
        "business_domain": focus.business_domain,
        "capability": focus.capability,
        "status": focus.status,
        "strategic_impact": focus.strategic_impact,
        "economic_potential": focus.economic_potential,
        "pain_intensity": focus.pain_intensity,
        "data_accessibility": focus.data_accessibility,
        "change_effort": focus.change_effort,
        "rationale": focus.rationale,
    }
    expected_values = {
        "business_domain": expected["business_domain"],
        "capability": expected["capability"],
        "status": expected["status"],
        "strategic_impact": "",
        "economic_potential": "",
        "pain_intensity": "",
        "data_accessibility": "",
        "change_effort": "",
        "rationale": "",
    }
    return _object_diff(
        "value_stream_focus",
        "focus",
        focus,
        current,
        expected_values,
    )


def _stage_values(stage: ValueStreamStage) -> dict[str, Any]:
    return {
        "sequence": stage.sequence,
        "name": stage.name,
        "description": stage.description,
        "actors": stage.actors,
        "systems": stage.systems,
        "documents": stage.documents,
        "pain_points": stage.pain_points,
        "baseline_metrics": stage.baseline_metrics,
    }


def _process_values(process: ProcessAnalysis) -> dict[str, Any]:
    return {
        "name": process.name,
        "status": process.status,
        "scope_start": process.scope_start,
        "scope_end": process.scope_end,
        "trigger": process.trigger,
        "outcome": process.outcome,
        "current_flow": process.current_flow,
        "roles": process.roles,
        "systems": process.systems,
        "data_objects": process.data_objects,
        "business_rules": process.business_rules,
        "handoffs": process.handoffs,
        "bottlenecks": process.bottlenecks,
        "exceptions": process.exceptions,
        "baseline_metrics": process.baseline_metrics,
        "target_state_principles": process.target_state_principles,
    }


def _option_values(option: SolutionOption) -> dict[str, Any]:
    return {
        "name": option.name,
        "option_type": option.option_type,
        "recommendation": option.recommendation,
        "evaluation_status": option.evaluation_status,
        "description": option.description,
        "expected_value": option.expected_value,
        "bottleneck_coverage": option.bottleneck_coverage,
        "feasibility": option.feasibility,
        "data_requirements": option.data_requirements,
        "application_impact": option.application_impact,
        "integration_effort": option.integration_effort,
        "integration_impact": option.integration_impact,
        "technology_constraints": option.technology_constraints,
        "risks": option.risks,
        "architecture_fit": option.architecture_fit,
    }


def _use_case_values(use_case: UseCase) -> dict[str, Any]:
    return {
        "title": use_case.title,
        "status": use_case.status,
        "decision_status": use_case.decision_status,
        "summary": use_case.summary,
        "problem_statement": use_case.problem_statement,
        "business_unit": use_case.business_unit_id,
        "affected_process": use_case.affected_process,
        "target_users": use_case.target_users,
        "submitter": use_case.submitter_id,
        "business_owner": use_case.business_owner_id,
        "coordinator": use_case.coordinator_id,
        "technical_owner": use_case.technical_owner_id,
        "priority": use_case.priority,
        "solution_type": use_case.solution_type,
        "hosting_type": use_case.hosting_type,
        "provider": use_case.provider,
        "product_name": use_case.product_name,
        "model_name": use_case.model_name,
        "source_systems": use_case.source_systems,
        "data_sources": use_case.data_sources,
        "interface_description": use_case.interface_description,
        "intended_users": use_case.intended_users,
        "intended_purpose": use_case.intended_purpose,
        "expected_benefit": use_case.expected_benefit,
        "benefit_category": use_case.benefit_category,
        "metric_name": use_case.metric_name,
        "metric_type": use_case.metric_type,
        "metric_direction": use_case.metric_direction,
        "metric_unit": use_case.metric_unit,
        "metric_baseline": use_case.metric_baseline,
        "metric_target": use_case.metric_target,
        "metric_measurement_method": use_case.metric_measurement_method,
        "one_time_cost": use_case.one_time_cost,
        "recurring_cost": use_case.recurring_cost,
        "business_value": use_case.business_value,
        "technical_feasibility": use_case.technical_feasibility,
        "data_readiness": use_case.data_readiness,
        "risk_complexity": use_case.risk_complexity,
        "human_oversight": use_case.human_oversight,
        "support_responsibility": use_case.support_responsibility,
    }


def _expected_use_case(resolved: ResolvedBlueprint) -> dict[str, Any]:
    data = resolved.payload["use_case"]
    metric = data["metric"]
    return {
        "title": data["title"],
        "status": data["status"],
        "decision_status": data["decision_status"],
        "summary": data["summary"],
        "problem_statement": data["problem_statement"],
        "business_unit": resolved.business_unit.pk,
        "affected_process": data["affected_process"],
        "target_users": data["target_users"],
        "submitter": resolved.actors["creator"].pk,
        "business_owner": resolved.actors["business_owner"].pk,
        "coordinator": resolved.actors["coordinator"].pk,
        "technical_owner": resolved.actors["technical_owner"].pk,
        "priority": data["priority"],
        "solution_type": data["solution_type"],
        "hosting_type": data["hosting_type"],
        "provider": data["provider"],
        "product_name": data["product_name"],
        "model_name": data["model_name"],
        "source_systems": data["source_systems"],
        "data_sources": data["data_sources"],
        "interface_description": data["interface_description"],
        "intended_users": data["intended_users"],
        "intended_purpose": data["intended_purpose"],
        "expected_benefit": data["expected_benefit"],
        "benefit_category": data["benefit_category"],
        "metric_name": metric["name"],
        "metric_type": metric["type"],
        "metric_direction": metric["direction"],
        "metric_unit": metric["unit"],
        "metric_baseline": metric["baseline"],
        "metric_target": metric["target"],
        "metric_measurement_method": metric["measurement_method"],
        "one_time_cost": data["one_time_cost"],
        "recurring_cost": data["recurring_cost"],
        "business_value": data["business_value"],
        "technical_feasibility": data["technical_feasibility"],
        "data_readiness": data["data_readiness"],
        "risk_complexity": data["risk_complexity"],
        "human_oversight": data["human_oversight"],
        "support_responsibility": data["support_responsibility"],
    }


def _classification_diff(
    use_case: UseCase | None, resolved: ResolvedBlueprint
) -> ObjectDifference:
    expected = resolved.payload["use_case"]["classification"]
    if use_case is None:
        return ObjectDifference("use_case_classification", "classification", DiffStatus.CREATE)
    try:
        classification = use_case.classification
    except ObjectDoesNotExist:
        return ObjectDifference(
            "use_case_classification",
            "classification",
            DiffStatus.CONFLICT,
        )
    current = {
        "business_domain": classification.business_domain,
        "capability": classification.capability,
        "process_area": classification.process_area,
    }
    return _object_diff(
        "use_case_classification",
        "classification",
        classification,
        current,
        expected,
    )


def _red_state_differences(
    stream: ValueStream | None,
    process: ProcessAnalysis | None,
    options: list[SolutionOption],
    use_case: UseCase | None,
) -> list[ObjectDifference]:
    result = []
    if process is not None and ProcessValidation.objects.filter(
        process_analysis=process
    ).exists():
        result.append(
            ObjectDifference("process_validation", "forbidden", DiffStatus.CONFLICT)
        )
    if process is not None and SolutionSelectionDecision.objects.filter(
        process_analysis=process
    ).exists():
        result.append(
            ObjectDifference(
                "solution_selection_decision",
                "forbidden",
                DiffStatus.CONFLICT,
            )
        )
    if any(option.recommendation != SolutionOption.Recommendation.CANDIDATE for option in options):
        result.append(
            ObjectDifference("solution_preference", "forbidden", DiffStatus.CONFLICT)
        )
    if use_case is not None:
        forbidden_counts = {
            "decision_assessment": DecisionAssessment.objects.filter(
                use_case=use_case
            ).count(),
            "approval_decision": ApprovalDecision.objects.filter(use_case=use_case).count(),
            "governance_assessment": GovernanceAssessment.objects.filter(
                use_case=use_case
            ).count(),
            "delivery_package": DeliveryPackage.objects.filter(use_case=use_case).count(),
        }
        for object_type, count in sorted(forbidden_counts.items()):
            if count:
                result.append(
                    ObjectDifference(object_type, "forbidden", DiffStatus.CONFLICT)
                )
        lifecycle_fields = {
            "pilot_start": use_case.pilot_start,
            "actual_end_date": use_case.actual_end_date,
            "metric_actual": use_case.metric_actual,
            "metric_measured_at": use_case.metric_measured_at,
            "realized_result": use_case.realized_result,
            "ending_reason": use_case.ending_reason,
            "is_archived": use_case.is_archived,
        }
        differences = tuple(
            FieldDifference(field, _display(value), None)
            for field, value in sorted(lifecycle_fields.items())
            if value not in (None, "", False)
        )
        if differences:
            result.append(
                ObjectDifference(
                    "use_case_lifecycle",
                    "forbidden",
                    DiffStatus.CONFLICT,
                    differences,
                )
            )
    if stream is not None and stream.status != ValueStream.Status.DRAFT:
        result.append(
            ObjectDifference("value_stream_state", "forbidden", DiffStatus.CONFLICT)
        )
    return result


def build_blueprint_diff(resolved: ResolvedBlueprint) -> BlueprintGraphDiff:
    payload = resolved.payload
    stream_data = payload["value_stream"]
    use_case_data = payload["use_case"]
    stream = ValueStream.objects.filter(demo_key=stream_data["key"]).first()
    use_case = UseCase.objects.filter(demo_key=use_case_data["key"]).first()

    objects: list[ObjectDifference] = []
    stream_name_collision = ValueStream.objects.filter(name=stream_data["name"]).exclude(
        demo_key=stream_data["key"]
    )
    if stream is None and stream_name_collision.exists():
        objects.append(
            ObjectDifference("value_stream", stream_data["key"], DiffStatus.CONFLICT)
        )
    else:
        objects.append(
            _object_diff(
                "value_stream",
                stream_data["key"],
                stream,
                _stream_values(stream) if stream is not None else None,
                _expected_stream(resolved),
            )
        )
    objects.append(_focus_diff(stream, resolved))

    stages_by_sequence = {
        stage.sequence: stage for stage in stream.stages.all()
    } if stream is not None else {}
    stage_by_key: dict[str, ValueStreamStage | None] = {}
    for stage_data in sorted(stream_data["stages"], key=lambda item: item["sequence"]):
        stage = stages_by_sequence.get(stage_data["sequence"])
        stage_by_key[stage_data["key"]] = stage
        objects.append(
            _object_diff(
                "value_stream_stage",
                stage_data["key"],
                stage,
                _stage_values(stage) if stage is not None else None,
                {
                    key: stage_data[key]
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
                },
            )
        )
    if stream is not None and len(stages_by_sequence) != len(stream_data["stages"]):
        objects.append(
            ObjectDifference("value_stream_stages", "cardinality", DiffStatus.CONFLICT)
        )

    process_data = payload["process_analysis"]
    process_stage = stage_by_key.get(process_data["stage_key"])
    process = None
    if process_stage is not None:
        process = ProcessAnalysis.objects.filter(
            stage=process_stage,
            name=process_data["name"],
        ).first()
    objects.append(
        _object_diff(
            "process_analysis",
            process_data["key"],
            process,
            _process_values(process) if process is not None else None,
            {
                key: process_data[key]
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
            },
        )
    )

    current_options = list(process.solution_options.all()) if process is not None else []
    options_by_name = {option.name: option for option in current_options}
    selected_option: SolutionOption | None = None
    for option_data in sorted(payload["solution_options"], key=lambda item: item["key"]):
        option = options_by_name.get(option_data["name"])
        if option_data["key"] == payload["origin"]["solution_option_key"]:
            selected_option = option
        objects.append(
            _object_diff(
                "solution_option",
                option_data["key"],
                option,
                _option_values(option) if option is not None else None,
                {
                    key: option_data[key]
                    for key in (
                        "name",
                        "option_type",
                        "recommendation",
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
                },
            )
        )
    if process is not None and len(current_options) != len(payload["solution_options"]):
        objects.append(
            ObjectDifference("solution_options", "cardinality", DiffStatus.CONFLICT)
        )

    use_case_title_collision = UseCase.objects.filter(title=use_case_data["title"]).exclude(
        demo_key=use_case_data["key"]
    )
    if use_case is None and use_case_title_collision.exists():
        objects.append(
            ObjectDifference("use_case", use_case_data["key"], DiffStatus.CONFLICT)
        )
    else:
        objects.append(
            _object_diff(
                "use_case",
                use_case_data["key"],
                use_case,
                _use_case_values(use_case) if use_case is not None else None,
                _expected_use_case(resolved),
            )
        )
    objects.append(_classification_diff(use_case, resolved))

    origin = None
    if use_case is not None:
        origin = UseCaseOrigin.objects.filter(use_case=use_case).first()
    expected_origin = {
        "stage": process_stage.pk if process_stage is not None else None,
        "process_analysis": process.pk if process is not None else None,
        "solution_option": selected_option.pk if selected_option is not None else None,
    }
    current_origin = None
    if origin is not None:
        current_origin = {
            "stage": origin.stage_id,
            "process_analysis": origin.process_analysis_id,
            "solution_option": origin.solution_option_id,
        }
    objects.append(
        _object_diff(
            "use_case_origin",
            "origin",
            origin,
            current_origin,
            expected_origin,
        )
    )
    objects.extend(_red_state_differences(stream, process, current_options, use_case))

    statuses = {item.status for item in objects}
    if DiffStatus.CREATE in statuses and DiffStatus.NO_CHANGE in statuses:
        objects.append(
            ObjectDifference("scenario_graph", "partial", DiffStatus.CONFLICT)
        )
    return BlueprintGraphDiff(
        scenario_key=payload["scenario_key"],
        schema_version=payload["schema_version"],
        checksum=resolved.checksum,
        objects=tuple(objects),
    )
