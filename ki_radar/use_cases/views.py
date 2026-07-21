from __future__ import annotations

import csv
import os
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ki_radar.accounts.models import BusinessUnit
from ki_radar.accounts.permissions import is_coordinator

from .blockers import build_blocker_details
from .copilot import CopilotUnavailable, analyze_use_case
from .forms import UseCaseForm
from .models import UseCase
from .permissions import can_create_use_case, can_edit_use_case, can_view_use_case
from .services import current_decision_check, decision_due_date


@login_required
def use_case_list(request):
    queryset = UseCase.objects.filter(is_archived=False).select_related(
        "business_unit", "business_owner", "coordinator"
    )
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(short_id__icontains=query)
            | Q(problem_statement__icontains=query)
            | Q(expected_benefit__icontains=query)
            | Q(metric_name__icontains=query)
        )

    for parameter, field_name in {
        "status": "status",
        "business_unit": "business_unit_id",
        "business_owner": "business_owner_id",
        "coordinator": "coordinator_id",
        "business_value": "business_value",
        "technical_feasibility": "technical_feasibility",
        "data_readiness": "data_readiness",
        "risk_complexity": "risk_complexity",
    }.items():
        value = request.GET.get(parameter)
        if value:
            queryset = queryset.filter(**{field_name: value})

    for parameter in [
        "privacy_review_required",
        "security_review_required",
        "legal_review_required",
    ]:
        if request.GET.get(parameter) == "1":
            queryset = queryset.filter(**{parameter: True})

    today = timezone.localdate()
    review_state = request.GET.get("review_state", "")
    if review_state == "overdue":
        queryset = queryset.filter(next_review_date__lt=today).exclude(status=UseCase.Status.ENDED)
    elif review_state == "due_30":
        queryset = queryset.filter(
            next_review_date__gte=today,
            next_review_date__lte=today + timedelta(days=30),
        ).exclude(status=UseCase.Status.ENDED)
    elif review_state == "missing":
        queryset = queryset.filter(next_review_date__isnull=True).exclude(
            status=UseCase.Status.ENDED
        )

    use_cases = list(queryset)
    for item in use_cases:
        item.decision_check = current_decision_check(item)
        item.blocker_details = build_blocker_details(item, item.decision_check.blockers)
        item.decision_due = decision_due_date(item)

    user_model = get_user_model()
    active_users = user_model.objects.filter(is_active=True, is_anonymized=False).order_by(
        "last_name", "first_name", "username"
    )
    context = {
        "use_cases": use_cases,
        "status_choices": UseCase.Status.choices,
        "level_choices": UseCase.Level.choices,
        "business_units": BusinessUnit.objects.filter(is_active=True).order_by("name"),
        "active_users": active_users,
        "can_create": can_create_use_case(request.user),
    }
    return render(request, "use_cases/list.html", context)


def _detail_context(request, use_case: UseCase, *, copilot_analysis: str = "") -> dict:
    history = use_case.history.select_related("history_user").order_by("-history_date")[:50]
    decision_check = current_decision_check(use_case)
    blocker_details = build_blocker_details(use_case, decision_check.blockers)
    return {
        "use_case": use_case,
        "history": history,
        "can_edit": can_edit_use_case(request.user, use_case),
        "decision_check": decision_check,
        "blocker_details": blocker_details,
        "first_blocker": blocker_details[0] if blocker_details else None,
        "decision_due": decision_due_date(use_case),
        "copilot_analysis": copilot_analysis,
        "copilot_enabled": bool(os.getenv("OPENROUTER_API_KEY")),
    }


@login_required
def use_case_detail(request, pk):
    use_case = get_object_or_404(
        UseCase.objects.select_related(
            "business_unit", "business_owner", "coordinator", "technical_owner"
        ).prefetch_related(
            "governance_assessments",
            "reviews",
            "evidence_links",
            "decision_assessments",
            "approval_decisions",
        ),
        pk=pk,
    )
    if not can_view_use_case(request.user, use_case):
        raise PermissionDenied
    return render(request, "use_cases/detail.html", _detail_context(request, use_case))


@login_required
@require_POST
def use_case_copilot(request, pk):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(
        UseCase.objects.select_related(
            "business_unit", "business_owner", "coordinator", "technical_owner"
        ).prefetch_related(
            "governance_assessments",
            "reviews",
            "evidence_links",
            "decision_assessments",
            "approval_decisions",
        ),
        pk=pk,
    )
    try:
        analysis = analyze_use_case(use_case)
    except CopilotUnavailable as exc:
        messages.warning(request, str(exc))
        analysis = ""
    return render(
        request,
        "use_cases/detail.html",
        _detail_context(request, use_case, copilot_analysis=analysis),
    )


@login_required
def use_case_create(request):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = UseCaseForm(request.POST, current_user=request.user)
        if form.is_valid():
            use_case = form.save(commit=False)
            use_case.submitter = request.user
            use_case.save()
            messages.success(request, f"Use Case {use_case.short_id} wurde angelegt.")
            return redirect(use_case)
    else:
        form = UseCaseForm(current_user=request.user)
    return render(request, "use_cases/form.html", {"form": form, "title": "Use Case anlegen"})


@login_required
def use_case_edit(request, pk):
    use_case = get_object_or_404(UseCase, pk=pk)
    if not can_edit_use_case(request.user, use_case):
        raise PermissionDenied
    if request.method == "POST":
        form = UseCaseForm(request.POST, instance=use_case, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Use Case wurde aktualisiert.")
            return redirect(use_case)
    else:
        form = UseCaseForm(instance=use_case, current_user=request.user)
    requested_highlight = request.GET.get("highlight", "")
    highlight_field = requested_highlight if requested_highlight in form.fields else ""
    return render(
        request,
        "use_cases/form.html",
        {
            "form": form,
            "title": f"{use_case.short_id} bearbeiten",
            "use_case": use_case,
            "highlight_field": highlight_field,
        },
    )


@login_required
def export_csv(request):
    queryset = UseCase.objects.filter(is_archived=False).select_related(
        "business_unit", "business_owner"
    )
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="ki-radar-use-cases.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        [
            "ID",
            "Titel",
            "Status",
            "Organisationseinheit",
            "Business Owner",
            "Nächste Entscheidung",
            "Entscheidungsreife",
            "Primäre Metrik",
            "Baseline",
            "Ziel",
            "Ist",
            "Einheit",
            "Zielerreichung",
        ]
    )
    for use_case in queryset:
        decision = current_decision_check(use_case)
        writer.writerow(
            [
                use_case.short_id,
                use_case.title,
                use_case.get_status_display(),
                use_case.business_unit.name,
                use_case.business_owner.get_display_name(),
                decision.title,
                decision.state_label,
                use_case.metric_name,
                use_case.metric_baseline if use_case.metric_baseline is not None else "",
                use_case.metric_target if use_case.metric_target is not None else "",
                use_case.metric_actual if use_case.metric_actual is not None else "",
                use_case.metric_unit,
                use_case.metric_result_label,
            ]
        )
    return response
