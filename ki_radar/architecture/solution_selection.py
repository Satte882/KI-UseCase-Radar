from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from .focus import get_value_stream_focus
from .models import ProcessAnalysis, SolutionOption, SolutionSelectionDecision
from .permissions import can_edit_value_stream

OPTION_TYPE_PRIORITY = {
    SolutionOption.OptionType.NO_TECH: 0,
    SolutionOption.OptionType.ORGANIZATIONAL: 1,
    SolutionOption.OptionType.RULE_AUTOMATION: 2,
    SolutionOption.OptionType.STANDARD_SOFTWARE: 3,
    SolutionOption.OptionType.CUSTOM_SOFTWARE: 4,
    SolutionOption.OptionType.ANALYTICS_ML: 5,
    SolutionOption.OptionType.GENERATIVE_AI: 6,
    SolutionOption.OptionType.ASSISTANT: 7,
    SolutionOption.OptionType.OTHER: 8,
}


def ordered_solution_options(process_analysis: ProcessAnalysis) -> list[SolutionOption]:
    return sorted(
        process_analysis.solution_options.all(),
        key=lambda option: (
            OPTION_TYPE_PRIORITY.get(option.option_type, 99),
            option.name.casefold(),
            str(option.pk),
        ),
    )


def comparison_blockers(options: list[SolutionOption]) -> list[str]:
    blockers: list[str] = []
    if len(options) < 2:
        blockers.append("Mindestens zwei unterschiedliche Lösungsoptionen sind erforderlich.")
    incomplete = [option.name for option in options if not option.comparison_complete]
    if incomplete:
        blockers.append(
            "Folgende Optionen sind noch nicht vollständig bewertet: " + ", ".join(incomplete)
        )
    return blockers


def build_comparison_snapshot(options: list[SolutionOption]) -> list[dict]:
    return [
        {
            "id": str(option.pk),
            "name": option.name,
            "option_type": option.option_type,
            "option_type_label": option.get_option_type_display(),
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
            "updated_at": option.updated_at.isoformat(),
        }
        for option in options
    ]


@transaction.atomic
def select_preferred_solution(
    *,
    process_analysis: ProcessAnalysis,
    selected_option: SolutionOption,
    rationale: str,
    actor,
) -> SolutionSelectionDecision:
    process_analysis = (
        ProcessAnalysis.objects.select_for_update()
        .select_related("stage__value_stream__focus")
        .get(pk=process_analysis.pk)
    )
    if not can_edit_value_stream(actor, process_analysis.stage.value_stream):
        raise ValidationError("Für diese Lösungsentscheidung fehlt die Berechtigung.")
    focus = get_value_stream_focus(process_analysis.stage.value_stream)
    if focus is None or not focus.is_selected:
        raise ValidationError(
            "Eine bevorzugte Option kann erst nach einer dokumentierten "
            "Fokusentscheidung gewählt werden."
        )
    options = ordered_solution_options(process_analysis)
    blockers = comparison_blockers(options)
    if blockers:
        raise ValidationError(" | ".join(blockers))
    selected = next((option for option in options if option.pk == selected_option.pk), None)
    if selected is None:
        raise ValidationError("Die gewählte Option gehört nicht zu dieser Prozessanalyse.")
    reason = rationale.strip()
    if not reason:
        raise ValidationError("Für die Auswahl ist eine Begründung erforderlich.")

    decision = SolutionSelectionDecision.objects.create(
        process_analysis=process_analysis,
        selected_option=selected,
        rationale=reason,
        comparison_snapshot=build_comparison_snapshot(options),
        decided_by=actor,
    )
    process_analysis.solution_options.exclude(pk=selected.pk).update(
        recommendation=SolutionOption.Recommendation.REJECTED
    )
    selected.recommendation = SolutionOption.Recommendation.PREFERRED
    selected.save(update_fields=["recommendation", "updated_at"])
    return decision
