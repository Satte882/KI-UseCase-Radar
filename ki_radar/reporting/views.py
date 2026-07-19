from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.services import (
    current_decision_check,
    decision_due_date,
    decision_priority,
)


@login_required
def dashboard(request):
    today = timezone.localdate()
    active_qs = (
        UseCase.objects.filter(is_archived=False)
        .exclude(status=UseCase.Status.ENDED)
        .select_related("business_owner", "business_unit", "technical_owner")
        .prefetch_related("governance_assessments")
    )
    active = list(active_qs)
    for item in active:
        item.decision_check = current_decision_check(item)
        item.decision_due = decision_due_date(item)
    decision_queue = sorted(active, key=decision_priority)

    status_counts = {
        row["status"]: row["total"]
        for row in UseCase.objects.filter(is_archived=False)
        .values("status")
        .annotate(total=Count("id"))
    }
    blocked = sum(item.decision_check.state == "blocked" for item in active)
    overdue = sum(item.decision_due is not None and item.decision_due < today for item in active)
    measured = sum(item.metric_actual is not None for item in active)
    achieved = sum(item.metric_result == UseCase.MetricResult.ACHIEVED for item in active)

    context = {
        "status_counts": status_counts,
        "decision_queue": decision_queue[:20],
        "active_total": len(active),
        "blocked_total": blocked,
        "overdue_total": overdue,
        "measured_total": measured,
        "achieved_total": achieved,
        "due_soon_total": sum(
            item.decision_due is not None
            and today <= item.decision_due <= today + timedelta(days=30)
            for item in active
        ),
        "today": today,
    }
    return render(request, "reporting/dashboard.html", context)
