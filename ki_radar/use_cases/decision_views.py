from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ki_radar.accounts.permissions import is_coordinator

from .blockers import build_blocker_details
from .decision_forms import ApprovalDecisionForm, DecisionAssessmentForm
from .models import ApprovalDecision, UseCase
from .services import (
    approval_check,
    confirm_conditional_decision,
    create_decision_assessment,
    submit_approval_decision,
)


@login_required
def assessment_create(request, pk):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(UseCase, pk=pk)
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
            return redirect(use_case)
    else:
        form = DecisionAssessmentForm()
    return render(
        request,
        "use_cases/assessment_form.html",
        {"form": form, "use_case": use_case},
    )


@login_required
def approval_decision_create(request, pk):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(
        UseCase.objects.prefetch_related("decision_assessments", "approval_decisions"),
        pk=pk,
    )
    assessment = use_case.decision_assessments.first()
    if assessment is None:
        messages.warning(request, "Vor einer Entscheidung ist eine strukturierte Bewertung nötig.")
        return redirect("use_cases:assessment_create", pk=use_case.pk)

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
                return redirect(use_case)
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
    return render(
        request,
        "use_cases/decision_form.html",
        {
            "form": form,
            "use_case": use_case,
            "assessment": assessment,
            "approval_check": check,
            "approval_blocker_details": blocker_details,
            "first_approval_blocker": blocker_details[0] if blocker_details else None,
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
        messages.error(request, str(exc))
    else:
        messages.success(request, "Die zweite Freigabe wurde bestätigt.")
    return redirect(decision.use_case)
