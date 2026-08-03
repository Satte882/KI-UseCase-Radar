from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.accounts.models import BusinessUnit
from ki_radar.architecture.provenance import stored_provenance_rows
from ki_radar.core.taxonomy import BusinessDomain

from .intake import WIZARD_STEPS
from .models import UseCase
from .permissions import can_create_use_case
from .services import intake_blockers

SESSION_KEY = "use_case_intake"
STEP_LABELS = {
    1: "Problem",
    2: "Prozess",
    3: "Nutzung",
    4: "Nutzen",
    5: "Daten",
    6: "Vorprüfung",
}


def _serialize_cleaned_data(cleaned_data: dict) -> dict:
    serialized = {}
    for key, value in cleaned_data.items():
        if isinstance(value, BusinessUnit):
            serialized[key] = value.pk
        elif isinstance(value, Decimal):
            serialized[key] = str(value)
        else:
            serialized[key] = value
    return serialized


def _form_initial(step: int, stored: dict) -> dict:
    fields = WIZARD_STEPS[step]["form"].base_fields
    return {name: stored[name] for name in fields if name in stored}


def _wizard_step_states(
    *,
    stored: dict,
    current_step: int,
    error_step: int | None = None,
) -> list[dict]:
    states = []
    for number in WIZARD_STEPS:
        form_class = WIZARD_STEPS[number]["form"]
        complete = number == 6 and current_step == 6
        if form_class is not None:
            complete = all(name in stored for name in form_class.base_fields)
        if number == error_step:
            state = "error"
            symbol = "!"
        elif complete:
            state = "complete"
            symbol = "✓"
        else:
            state = "pending"
            symbol = str(number)
        states.append(
            {
                "number": number,
                "label": STEP_LABELS[number],
                "state": state,
                "symbol": symbol,
                "is_current": number == current_step,
                "is_reachable": number <= current_step,
            }
        )
    return states


def _build_use_case(*, stored: dict, user) -> UseCase:
    candidate = UseCase(
        title=stored["title"],
        summary=stored["summary"],
        problem_statement=stored["problem_statement"],
        business_unit=get_object_or_404(BusinessUnit, pk=stored["business_unit"]),
        affected_process=stored["affected_process"],
        target_users=stored["target_users"],
        submitter=user,
        business_owner=user,
        source_systems=stored.get("source_systems", ""),
        data_sources=stored["data_sources"],
        intended_users=stored["intended_users"],
        intended_purpose=stored["intended_purpose"],
        expected_benefit=stored["expected_benefit"],
        metric_name=stored["metric_name"],
        metric_type=stored["metric_type"],
        metric_direction=stored["metric_direction"],
        metric_unit=stored["metric_unit"],
        metric_baseline=Decimal(stored["metric_baseline"]),
        metric_target=Decimal(stored["metric_target"]),
        metric_measurement_method=stored["metric_measurement_method"],
        privacy_review_required=stored.get("privacy_review_required", False),
        security_review_required=stored.get("security_review_required", False),
        legal_review_required=stored.get("legal_review_required", False),
        solution_type=stored["solution_type"],
        hosting_type=stored["hosting_type"],
        decision_status=UseCase.DecisionStatus.READY,
    )
    candidate._classification_payload = {
        "business_domain": stored.get("business_domain", BusinessDomain.OTHER),
        "capability": stored.get("business_capability", ""),
        "process_area": stored["affected_process"],
    }
    return candidate


def _persist_optional_origin(*, candidate: UseCase, stored: dict) -> None:
    source_stage_id = stored.get("source_stage_id")
    if not source_stage_id:
        return
    from ki_radar.architecture.models import (
        ProcessAnalysis,
        SolutionOption,
        UseCaseOrigin,
        ValueStreamStage,
    )

    stage = ValueStreamStage.objects.filter(pk=source_stage_id).first()
    if stage is None:
        return
    process_analysis = None
    source_process_id = stored.get("source_process_analysis_id")
    if source_process_id:
        process_analysis = ProcessAnalysis.objects.filter(
            pk=source_process_id,
            stage=stage,
        ).first()
    solution_option = None
    source_option_id = stored.get("source_solution_option_id")
    if source_option_id and process_analysis is not None:
        solution_option = SolutionOption.objects.filter(
            pk=source_option_id,
            process_analysis=process_analysis,
        ).first()
    UseCaseOrigin.objects.create(
        use_case=candidate,
        stage=stage,
        process_analysis=process_analysis,
        solution_option=solution_option,
        source_manifest=stored.get("_source_manifest", {}),
    )


@login_required
def use_case_intake(request, step: int = 1):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    if step not in WIZARD_STEPS:
        return redirect("use_cases:create")

    stored = request.session.get(SESSION_KEY, {})
    step_config = WIZARD_STEPS[step]
    form_class = step_config["form"]
    progress_class = f"wizard-progress-{step}"

    if step == 6:
        required_steps_complete = all(
            all(name in stored for name in WIZARD_STEPS[number]["form"].base_fields)
            for number in range(1, 6)
        )
        if not required_steps_complete:
            messages.warning(request, "Die Aufnahme ist noch nicht vollständig.")
            return redirect("use_cases:create")
        candidate = _build_use_case(stored=stored, user=request.user)
        blockers = intake_blockers(candidate)
        if request.method == "POST":
            if blockers:
                messages.error(
                    request,
                    "Der Use Case ist noch nicht bewertbar: " + ", ".join(blockers),
                )
            else:
                candidate._history_user = request.user
                candidate.save()
                _persist_optional_origin(candidate=candidate, stored=stored)
                request.session.pop(SESSION_KEY, None)
                messages.success(
                    request,
                    f"Use Case {candidate.short_id} ist bereit zur Bewertung.",
                )
                return redirect(candidate)
        return render(
            request,
            "use_cases/intake_wizard.html",
            {
                "step": step,
                "step_config": step_config,
                "total_steps": len(WIZARD_STEPS),
                "progress_class": progress_class,
                "step_states": _wizard_step_states(stored=stored, current_step=step),
                "stored": stored,
                "candidate": candidate,
                "blockers": blockers,
                "source_context": stored_provenance_rows(stored),
            },
        )

    error_step = None
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            stored.update(_serialize_cleaned_data(form.cleaned_data))
            request.session[SESSION_KEY] = stored
            request.session.modified = True
            return redirect("use_cases:intake_step", step=step + 1)
        error_step = step
    else:
        form = form_class(initial=_form_initial(step, stored))

    return render(
        request,
        "use_cases/intake_wizard.html",
        {
            "form": form,
            "step": step,
            "step_config": step_config,
            "total_steps": len(WIZARD_STEPS),
            "progress_class": progress_class,
            "step_states": _wizard_step_states(
                stored=stored,
                current_step=step,
                error_step=error_step,
            ),
            "previous_step": step - 1 if step > 1 else None,
        },
    )
