from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from ki_radar.use_cases.models import UseCase


@login_required
def dashboard(request):
    today = timezone.localdate()
    active = UseCase.objects.filter(is_archived=False).exclude(status=UseCase.Status.ENDED)
    context = {
        "status_counts": UseCase.objects.filter(is_archived=False)
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status"),
        "active_pilots": active.filter(status=UseCase.Status.PILOT).select_related(
            "business_owner"
        )[:10],
        "operations": active.filter(status=UseCase.Status.OPERATION).select_related(
            "business_owner"
        )[:10],
        "overdue": active.filter(next_review_date__lt=today).select_related("business_owner")[:20],
        "upcoming": active.filter(
            next_review_date__gte=today, next_review_date__lte=today + timedelta(days=30)
        ).select_related("business_owner")[:20],
        "missing_owner": UseCase.objects.filter(is_archived=False, business_owner__isnull=True),
        "missing_governance": active.filter(governance_assessments__isnull=True).distinct()[:20],
        "missing_technical_owner": active.filter(
            status=UseCase.Status.OPERATION, technical_owner__isnull=True
        )[:20],
        "stale": active.filter(updated_at__date__lt=today - timedelta(days=60))[:20],
        "today": today,
    }
    return render(request, "reporting/dashboard.html", context)
