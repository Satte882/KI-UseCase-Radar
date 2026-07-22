from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from ki_radar.core.taxonomy import BusinessDomain
from ki_radar.delivery.models import DeliveryPackage
from ki_radar.use_cases.blockers import build_blocker_details
from ki_radar.use_cases.classification import UseCaseClassification
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.outcome_workspace import (
    OUTCOME_STAGES,
    build_outcome_workspace_journey,
    normalize_outcome_stage,
    normalize_workspace_layout,
    outcome_workspace_url,
)
from ki_radar.use_cases.services import (
    current_decision_check,
    decision_due_date,
    decision_priority,
)
from ki_radar.use_cases.workflow import build_use_case_journey

from .portfolio import build_portfolio_context

OUTCOME_STAGE_COPY = {
    "pilot": {
        "title": "Piloten",
        "purpose": "Laufende oder übergebene Vorhaben für den nächsten Review sichtbar machen.",
        "ki_radar": "Review-Termin, Zielmetrik, Status-Snapshot und Link zum Delivery-System.",
        "external": "Backlog, Tasks, Sprints, technische Detailprobleme und täglicher Fortschritt.",
    },
    "effect": {
        "title": "Wirkung",
        "purpose": "Baseline, Ziel, Ist-Wert und belastbaren Messnachweis zusammenführen.",
        "ki_radar": "Entscheidungsrelevanter Mess-Snapshot zum vereinbarten Review-Zeitpunkt.",
        "external": "Operative Messdatenerhebung, technische Telemetrie und Rohdatenaufbereitung.",
    },
    "decision": {
        "title": "Ergebnisentscheidung",
        "purpose": "Scale-, Continue-, Nachbesserungs- oder Stop-Entscheidung vorbereiten.",
        "ki_radar": "Evidenz, Empfehlung, Begründung und später ein versioniertes Review-Artefakt.",
        "external": "Umsetzungsplanung der beschlossenen Maßnahmen oder Skalierung.",
    },
    "operation": {
        "title": "Betrieb",
        "purpose": "Verantwortung und wiederkehrende Management-Reviews sichtbar machen.",
        "ki_radar": "Owner, nächster Review, Nutzenstatus und entscheidungsrelevante Auflagen.",
        "external": "Incident-, Change-, Release- und Service-Management.",
    },
    "closure": {
        "title": "Abschluss",
        "purpose": "Beendigung, Datenbehandlung und Lessons Learned nachvollziehbar machen.",
        "ki_radar": "Abschlussentscheidung, Ergebnis, Beendigungsgrund und Lessons Learned.",
        "external": "Technische Stilllegung, Archivierung und operative Restarbeiten.",
    },
}


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


@login_required
def outcome_workspace(request):
    active_stage = normalize_outcome_stage(request.GET.get("stage"))
    layout = normalize_workspace_layout(request.GET.get("layout"))
    use_cases = list(
        UseCase.objects.filter(is_archived=False)
        .select_related("business_owner", "technical_owner", "business_unit")
        .prefetch_related("delivery_packages")
        .order_by("-updated_at")
    )
    for use_case in use_cases:
        use_case.latest_delivery = use_case.delivery_packages.first()

    requested_use_case = request.GET.get("use_case")
    selected_use_case = next(
        (item for item in use_cases if str(item.pk) == requested_use_case),
        None,
    )
    if selected_use_case is None:
        selected_use_case = next(
            (item for item in use_cases if item.status == UseCase.Status.PILOT),
            None,
        )
    if selected_use_case is None:
        selected_use_case = next(
            (
                item
                for item in use_cases
                if item.latest_delivery
                and item.latest_delivery.status == DeliveryPackage.Status.HANDED_OVER
            ),
            use_cases[0] if use_cases else None,
        )

    journey = (
        build_outcome_workspace_journey(
            selected_use_case,
            request.user,
            layout=layout,
        )
        if selected_use_case
        else None
    )
    stage_links = [
        {
            "key": stage,
            "label": label,
            "url": outcome_workspace_url(
                stage,
                use_case=selected_use_case,
                layout=layout,
            ),
        }
        for stage, label, _step_key in OUTCOME_STAGES
    ]
    layout_links = {
        "split": outcome_workspace_url(
            active_stage,
            use_case=selected_use_case,
            layout="split",
        ),
        "continuous": outcome_workspace_url(
            active_stage,
            use_case=selected_use_case,
            layout="continuous",
        ),
    }
    context = {
        "active_stage": active_stage,
        "active_stage_copy": OUTCOME_STAGE_COPY[active_stage],
        "journey": journey,
        "layout": layout,
        "layout_links": layout_links,
        "selected_use_case": selected_use_case,
        "stage_links": stage_links,
        "use_cases": use_cases,
        "pilot_total": sum(item.status == UseCase.Status.PILOT for item in use_cases),
        "measured_total": sum(item.metric_actual is not None for item in use_cases),
        "operation_total": sum(item.status == UseCase.Status.OPERATION for item in use_cases),
        "ended_total": sum(item.status == UseCase.Status.ENDED for item in use_cases),
    }
    return render(request, "reporting/outcome_workspace.html", context)
