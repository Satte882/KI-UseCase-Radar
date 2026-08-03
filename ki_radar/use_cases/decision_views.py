from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ki_radar.accounts.permissions import is_coordinator
from ki_radar.core.navigation import requested_return_to, with_return_to

from .blockers import build_blocker_details
from .decision_forms import ApprovalDecisionForm, DecisionAssessmentForm
from .models import ApprovalDecision, UseCase
from .services import (
    approval_check,
    confirm_conditional_decision,
    create_decision_assessment,
    submit_approval_decision,
)
from .status_dimensions import build_use_case_status_dimensions
from .workflow import build_use_case_journey


def _decision_use_case_queryset():
    return UseCase.objects.select_related(
        "business_unit",
        "business_owner",
        "coordinator",
        "technical_owner",
        "architecture_origin__stage__value_stream",
        "architecture_origin__stage__value_stream__focus",
        "architecture_origin__process_analysis",
        "architecture_origin__solution_option",
    ).prefetch_related(
        "governance_assessments",
        "decision_assessments",
        "approval_decisions",
        "delivery_packages",
    )


@login_required
def assessment_create(request, pk):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(_decision_use_case_queryset(), pk=pk)
    return_to = requested_return_to(request, use_case.get_absolute_url())
    if request.method == "POST":
        form = DecisionAssessmentForm(request.POST)
        if form.is_valid():
            assessment = create_decision_assessment(
                use_case=use_case,
                actor=request.user,
                data=form.cleaned_data,
            )
            messages.success(
                request,
                f"Bewertung v{assessment.version} wurde gespeichert. Confidence: "
                f"{assessment.confidence_label}.",
            )
            return redirect(return_to)
    else:
        form = DecisionAssessmentForm()
    journey = build_use_case_journey(use_case, request.user)
    return render(
        request,
        "use_cases/assessment_form.html",
        {
            "form": form,
            "use_case": use_case,
            "journey": journey,
            "status_dimensions": build_use_case_status_dimensions(use_case, journey),
            "return_to": return_to,
        },
    )


@login_required
def approval_decision_create(request, pk):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(_decision_use_case_queryset(), pk=pk)
    return_to = requested_return_to(request, use_case.get_absolute_url())
    assessment = use_case.decision_assessments.first()
    if assessment is None:
        messages.warning(request, "Vor einer Entscheidung ist eine strukturierte Bewertung nötig.")
        return redirect(
            with_return_to(
                reverse("use_cases:assessment_create", kwargs={"pk": use_case.pk}),
                return_to,
            )
        )

    if request.method == "POST":
        form = ApprovalDecisionForm(request.POST)
        if form.is_valid():
            try:
                decision = submit_approval_decision(
                    use_case=use_case,
                    actor=request.user,
                    data=form.cleaned_data,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                if decision.is_pending_second_approval:
                    messages.info(
                        request,
                        "Die Freigabe mit Auflagen wartet auf eine zweite unabhängige Bestätigung.",
                    )
                else:
                    messages.success(request, "Die Entscheidung wurde verbindlich gespeichert.")
                return redirect(return_to)
    else:
        form = ApprovalDecisionForm(initial={"decision_status": assessment.recommendation})

    selected_status = request.POST.get("decision_status", assessment.recommendation)
    check = approval_check(
        use_case=use_case,
        target_status=selected_status,
        actor=request.user,
        governance_confirmed=request.POST.get("governance_confirmed") == "on",
    )
    blocker_details = build_blocker_details(use_case, check.blockers)
    journey = build_use_case_journey(use_case, request.user)
    return render(
        request,
        "use_cases/decision_form.html",
        {
            "form": form,
            "use_case": use_case,
            "assessment": assessment,
            "journey": journey,
            "status_dimensions": build_use_case_status_dimensions(use_case, journey),
            "approval_check": check,
            "approval_blocker_details": blocker_details,
            "first_approval_blocker": blocker_details[0] if blocker_details else None,
            "return_to": return_to,
        },
    )


@login_required
@require_POST
def conditional_decision_confirm(request, decision_id):
    if not is_coordinator(request.user):
        raise PermissionDenied
    decision = get_object_or_404(
        ApprovalDecision.objects.select_related(
            "use_case", "assessment", "assessment__assessed_by", "decided_by"
        ),
        pk=decision_id,
    )
    try:
        confirm_conditional_decision(decision=decision, actor=request.user)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages) if exc.messages else str(exc))
    else:
        messages.success(request, "Die zweite Freigabe wurde bestätigt.")
    return redirect(decision.use_case)
