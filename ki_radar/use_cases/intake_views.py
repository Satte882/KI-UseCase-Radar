from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.accounts.models import BusinessUnit

from .intake import WIZARD_STEPS
from .models import UseCase
from .permissions import can_create_use_case
from .services import intake_blockers

SESSION_KEY = "use_case_intake"


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


def _build_use_case(*, stored: dict, user) -> UseCase:
    return UseCase(
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


@login_required
def use_case_intake(request, step: int = 1):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    if step not in WIZARD_STEPS:
        return redirect("use_cases:create")

    stored = request.session.get(SESSION_KEY, {})
    step_config = WIZARD_STEPS[step]
    form_class = step_config["form"]

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
                "stored": stored,
                "candidate": candidate,
                "blockers": blockers,
            },
        )

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            stored.update(_serialize_cleaned_data(form.cleaned_data))
            request.session[SESSION_KEY] = stored
            request.session.modified = True
            return redirect("use_cases:intake_step", step=step + 1)
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
            "previous_step": step - 1 if step > 1 else None,
        },
    )
