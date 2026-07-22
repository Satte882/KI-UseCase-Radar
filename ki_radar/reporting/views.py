from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from ki_radar.core.taxonomy import BusinessDomain
from ki_radar.use_cases.blockers import build_blocker_details
from ki_radar.use_cases.classification import UseCaseClassification
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.services import (
    current_decision_check,
    decision_due_date,
    decision_priority,
)
from ki_radar.use_cases.workflow import build_use_case_journey

from .portfolio import build_portfolio_context


@login_required
def dashboard(request):
    today = timezone.localdate()
    active_qs = (
        UseCase.objects.filter(is_archived=False)
        .exclude(status=UseCase.Status.ENDED)
        .select_related(
            "business_owner",
            "business_unit",
            "technical_owner",
            "classification",
            "architecture_origin__stage__value_stream",
            "architecture_origin__stage__value_stream__focus",
            "architecture_origin__process_analysis",
            "architecture_origin__solution_option",
        )
        .prefetch_related(
            "governance_assessments",
            "decision_assessments",
            "approval_decisions",
            "delivery_packages",
        )
    )
    active = list(active_qs)
    for item in active:
        item.decision_check = current_decision_check(item)
        item.blocker_details = build_blocker_details(item, item.decision_check.blockers)
        item.decision_due = decision_due_date(item)
        item.journey = build_use_case_journey(item, request.user)
    decision_queue = sorted(active, key=decision_priority)
    next_steps = [item for item in decision_queue if item.journey.next_action is not None]

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
        "next_steps": next_steps[:8],
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


@login_required
def portfolio(request):
    context = build_portfolio_context(request.GET)
    domain_labels = dict(BusinessDomain.choices)
    domain_rows = (
        UseCaseClassification.objects.filter(use_case__is_archived=False)
        .values("business_domain")
        .annotate(total=Count("use_case_id"))
        .order_by("business_domain")
    )
    context["business_domain_groups"] = [
        {
            "key": row["business_domain"],
            "label": domain_labels.get(row["business_domain"], "Nicht zugeordnet"),
            "total": row["total"],
        }
        for row in domain_rows
    ]
    return render(request, "reporting/portfolio.html", context)
