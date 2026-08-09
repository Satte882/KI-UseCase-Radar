import json

import pytest

from ki_radar.accelerator.solution_critic_contract import (
    CRITIC_CRITERIA,
    SolutionCriticContractError,
    build_solution_critic_json_schema,
    validate_solution_critic_payload,
)
from ki_radar.accelerator.solution_critic_prompt import (
    SOLUTION_CRITIC_SYSTEM_PROMPT,
    build_solution_critic_messages,
)
from ki_radar.accelerator.solution_generation_contract import (
    GENERATED_OPTION_FIELDS,
    OPTION_LANES,
    SOLUTION_GENERATION_SYSTEM_PROMPT,
)
from ki_radar.accelerator.solution_generation_sources import (
    SourceFact,
    SolutionGenerationSourceContext,
)
from ki_radar.accelerator.solution_quality_snapshot import SolutionQualitySnapshot
from ki_radar.accelerator.solution_quality_versions import (
    CRITIC_PROMPT_VERSION,
    CRITIC_SCHEMA_VERSION,
)


def source_context() -> SolutionGenerationSourceContext:
    return SolutionGenerationSourceContext(
        process_analysis_id="00000000-0000-0000-0000-000000000212",
        process_version=4,
        validation_state="current_validated",
        source_hash="a" * 64,
        missing_required=(),
        facts=(
            SourceFact(
                source_id="process.bottlenecks",
                field="bottlenecks",
                value="Die manuelle Angebotsprüfung ist der dokumentierte Engpass.",
            ),
            SourceFact(
                source_id="process.systems",
                field="systems",
                value="ERP-System",
            ),
        ),
    )


def payload_with(findings):
    return {
        "schema_version": CRITIC_SCHEMA_VERSION,
        "prompt_version": CRITIC_PROMPT_VERSION,
        "findings": findings,
    }


def finding(**overrides):
    value = {
        "criterion": "bottleneck_fit",
        "option": "assistant",
        "field": "bottleneck_coverage",
        "finding": "Der Entwurf adressiert den dokumentierten Engpass nicht konkret.",
        "source_ids": ["process.bottlenecks"],
        "repairable": True,
        "related_targets": [],
    }
    value.update(overrides)
    return value


def test_critic_criteria_are_exactly_the_five_v1_criteria() -> None:
    assert CRITIC_CRITERIA == (
        "distinctiveness",
        "bottleneck_fit",
        "grounding_consistency",
        "evidence_discipline",
        "complexity_proportionality",
    )


def test_empty_findings_are_valid() -> None:
    validated = validate_solution_critic_payload(payload_with([]), source_context())

    assert validated == {
        "schema_version": CRITIC_SCHEMA_VERSION,
        "prompt_version": CRITIC_PROMPT_VERSION,
        "findings": [],
    }


def test_valid_finding_gets_server_generated_stable_id() -> None:
    first = validate_solution_critic_payload(payload_with([finding()]), source_context())
    reordered_sources = finding(source_ids=["process.systems", "process.bottlenecks"])
    reordered_sources["finding"] = "Quellenbezug ist fachlich widersprüchlich."
    second = validate_solution_critic_payload(payload_with([reordered_sources]), source_context())
    third = validate_solution_critic_payload(payload_with([finding()]), source_context())

    finding_id = first["findings"][0]["finding_id"]
    assert finding_id.startswith("finding_")
    assert finding_id == third["findings"][0]["finding_id"]
    assert finding_id != second["findings"][0]["finding_id"]
    assert "finding_id" not in finding()


def test_source_order_does_not_change_finding_id() -> None:
    base = finding(
        criterion="grounding_consistency",
        source_ids=["process.bottlenecks", "process.systems"],
    )
    reversed_sources = finding(
        criterion="grounding_consistency",
        source_ids=["process.systems", "process.bottlenecks"],
    )

    first = validate_solution_critic_payload(payload_with([base]), source_context())
    second = validate_solution_critic_payload(payload_with([reversed_sources]), source_context())

    assert first["findings"][0]["finding_id"] == second["findings"][0]["finding_id"]
    assert first["findings"][0]["source_ids"] == ["process.bottlenecks", "process.systems"]


def test_cross_option_finding_can_authorize_multiple_explicit_targets() -> None:
    cross_option = finding(
        criterion="distinctiveness",
        option="organizational",
        field="description",
        finding="Organisations- und Assistenzentwurf unterscheiden sich fachlich nicht genug.",
        source_ids=[],
        related_targets=[
            {"option": "assistant", "field": "description"},
            {"option": "rule_automation", "field": "architecture_fit"},
        ],
    )

    validated = validate_solution_critic_payload(payload_with([cross_option]), source_context())

    result = validated["findings"][0]
    assert result["repairable"] is True
    assert result["field"] == "description"
    assert result["related_targets"] == [
        {"option": "rule_automation", "field": "architecture_fit"},
        {"option": "assistant", "field": "description"},
    ]


def test_repairable_finding_without_concrete_target_is_rejected() -> None:
    untargeted = finding()
    untargeted.pop("field")
    untargeted["related_targets"] = []

    with pytest.raises(SolutionCriticContractError) as exc_info:
        validate_solution_critic_payload(payload_with([untargeted]), source_context())

    assert "mindestens ein konkretes Feldziel" in str(exc_info.value)


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"criterion": "quality_score"}, "Nicht unterstützter Wert 'quality_score'"),
        ({"option": "preferred"}, "Nicht unterstützter Wert 'preferred'"),
        ({"field": "feasibility"}, "Nicht unterstützter Wert 'feasibility'"),
        ({"source_ids": ["process.unknown"]}, "nicht im Snapshot enthalten"),
    ],
)
def test_unknown_critic_references_are_rejected(override, expected) -> None:
    with pytest.raises(SolutionCriticContractError) as exc_info:
        validate_solution_critic_payload(payload_with([finding(**override)]), source_context())

    assert expected in str(exc_info.value)


def test_duplicate_target_is_rejected() -> None:
    duplicated = finding(
        related_targets=[{"option": "assistant", "field": "bottleneck_coverage"}]
    )

    with pytest.raises(SolutionCriticContractError) as exc_info:
        validate_solution_critic_payload(payload_with([duplicated]), source_context())

    assert "ist doppelt" in str(exc_info.value)


def test_identical_findings_are_rejected_as_ambiguous_repair_references() -> None:
    with pytest.raises(SolutionCriticContractError) as exc_info:
        validate_solution_critic_payload(payload_with([finding(), finding()]), source_context())

    assert "Identisches Finding" in str(exc_info.value)


def test_schema_contains_only_critic_fields_and_no_quality_score() -> None:
    schema = build_solution_critic_json_schema()
    serialized = json.dumps(schema, sort_keys=True)
    finding_schema = schema["properties"]["findings"]["items"]

    assert finding_schema["additionalProperties"] is False
    assert set(finding_schema["properties"]) == {
        "criterion",
        "option",
        "field",
        "finding",
        "source_ids",
        "repairable",
        "related_targets",
    }
    assert "quality_score" not in serialized
    assert "severity" not in serialized
    assert "confidence" not in serialized
    assert set(finding_schema["properties"]["option"]["enum"]) == set(OPTION_LANES)
    assert set(finding_schema["properties"]["field"]["enum"]) == set(GENERATED_OPTION_FIELDS)


def test_critic_prompt_is_separate_adversarial_and_non_decisional() -> None:
    assert SOLUTION_CRITIC_SYSTEM_PROMPT != SOLUTION_GENERATION_SYSTEM_PROMPT
    assert "adversariale Quality Critic" in SOLUTION_CRITIC_SYSTEM_PROMPT
    assert "semantischen Schwächen" in SOLUTION_CRITIC_SYSTEM_PROMPT
    assert "keinen Score" in SOLUTION_CRITIC_SYSTEM_PROMPT
    assert "keine Rangfolge" in SOLUTION_CRITIC_SYSTEM_PROMPT
    assert "keine bevorzugte Lösung" in SOLUTION_CRITIC_SYSTEM_PROMPT
    assert "leere Liste []" in SOLUTION_CRITIC_SYSTEM_PROMPT


def test_critic_messages_include_frozen_preview_and_source_context() -> None:
    snapshot = SolutionQualitySnapshot(
        snapshot_hash="b" * 64,
        document={"effective_payload": {"options": {"frozen": True}}},
    )

    messages = build_solution_critic_messages(snapshot, source_context())
    user_document = json.loads(messages[1]["content"])

    assert messages[0] == {"role": "system", "content": SOLUTION_CRITIC_SYSTEM_PROMPT}
    assert user_document["task"] == "semantic_solution_quality_critic"
    assert user_document["critic_schema_version"] == CRITIC_SCHEMA_VERSION
    assert user_document["critic_prompt_version"] == CRITIC_PROMPT_VERSION
    assert user_document["criteria"] == list(CRITIC_CRITERIA)
    assert user_document["quality_snapshot_hash"] == "b" * 64
    assert user_document["effective_preview"] == {"options": {"frozen": True}}
    assert user_document["source_data"]["facts"][0]["source_id"] == "process.bottlenecks"
