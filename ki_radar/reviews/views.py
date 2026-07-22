from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ki_radar.accounts.permissions import is_coordinator
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.outcome_workspace import outcome_workspace_url
from ki_radar.use_cases.permissions import can_start_pilot
from ki_radar.use_cases.services import current_decision_check

from .forms import ReviewForm
from .services import create_review


@login_required
def review_create(request, use_case_id):
    use_case = get_object_or_404(
        UseCase.objects.select_related("business_owner", "technical_owner").prefetch_related(
            "governance_assessments",
            "delivery_packages",
        ),
        pk=use_case_id,
    )
    coordinator_access = is_coordinator(request.user)
    pilot_start_only = request.GET.get("action") == "pilot_start" or not coordinator_access
    if pilot_start_only:
        if not can_start_pilot(request.user, use_case):
            raise PermissionDenied
    elif not coordinator_access:
        raise PermissionDenied

    if request.method == "POST":
        form = ReviewForm(
            request.POST,
            use_case=use_case,
            pilot_start_only=pilot_start_only,
        )
        if form.is_valid():
            try:
                create_review(use_case=use_case, actor=request.user, data=form.cleaned_data)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                if pilot_start_only:
                    messages.success(request, "Der Pilot wurde verbindlich gestartet.")
                    return redirect(outcome_workspace_url("pilot", use_case=use_case))
                messages.success(request, "Review und Entscheidung wurden gespeichert.")
                return redirect(use_case)
    else:
        form = ReviewForm(
            use_case=use_case,
            pilot_start_only=pilot_start_only,
        )
    return render(
        request,
        "reviews/form.html",
        {
            "form": form,
            "use_case": use_case,
            "decision_check": current_decision_check(use_case),
            "pilot_start_only": pilot_start_only,
        },
    )


@login_required
def monthly_review(request):
    if not is_coordinator(request.user):
        raise PermissionDenied
    today = timezone.localdate()
    queryset = (
        UseCase.objects.filter(is_archived=False)
        .exclude(status=UseCase.Status.ENDED)
        .select_related("business_owner", "business_unit")
    )
    context = {
        "today": today,
        "overdue": queryset.filter(next_review_date__lt=today),
        "due_soon": queryset.filter(
            next_review_date__gte=today, next_review_date__lte=today + timedelta(days=30)
        ),
        "missing_review_date": queryset.filter(next_review_date__isnull=True),
        "stale": queryset.filter(updated_at__date__lt=today - timedelta(days=60)),
        "pilots_without_result": queryset.filter(status=UseCase.Status.PILOT, metric_actual=None),
        "missing_governance": queryset.filter(governance_assessments__isnull=True).distinct(),
    }
    return render(request, "reviews/monthly.html", context)
