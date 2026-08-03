from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ki_radar.accounts.permissions import is_coordinator
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.status_dimensions import build_use_case_status_dimensions
from ki_radar.use_cases.workflow import build_use_case_journey

from .forms import GovernanceAssessmentForm, GovernanceReviewForm
from .models import GovernanceReview

REVIEW_CONFIG = {
    GovernanceReview.ReviewType.PRIVACY: {
        "label": "Datenschutzprüfung",
        "required_field": "privacy_review_required",
        "completed_field": "privacy_review_completed",
    },
    GovernanceReview.ReviewType.SECURITY: {
        "label": "Informationssicherheitsprüfung",
        "required_field": "security_review_required",
        "completed_field": "security_review_completed",
    },
    GovernanceReview.ReviewType.LEGAL: {
        "label": "Rechtsprüfung",
        "required_field": "legal_review_required",
        "completed_field": "legal_review_completed",
    },
}
REVIEW_ORDER = tuple(REVIEW_CONFIG)


def _next_required_review(use_case: UseCase) -> str | None:
    for review_type in REVIEW_ORDER:
        config = REVIEW_CONFIG[review_type]
        if getattr(use_case, config["required_field"]) and not getattr(
            use_case, config["completed_field"]
        ):
            return review_type
    return None


def _next_url(use_case: UseCase) -> str:
    next_review = _next_required_review(use_case)
    if next_review:
        return reverse(
            "governance:review",
            kwargs={"use_case_id": use_case.pk, "review_type": next_review},
        )
    if use_case.decision_assessments.exists():
        return reverse("use_cases:approval_decision_create", kwargs={"pk": use_case.pk})
    return use_case.get_absolute_url()


def _page_context(use_case: UseCase, user) -> dict:
    journey = build_use_case_journey(use_case, user)
    return {
        "journey": journey,
        "status_dimensions": build_use_case_status_dimensions(use_case, journey),
    }


@login_required
@transaction.atomic
def assessment_create(request, use_case_id):
    if not is_coordinator(request.user):
        raise PermissionDenied
    use_case = get_object_or_404(UseCase, pk=use_case_id)
    if request.method == "POST":
        form = GovernanceAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.use_case = use_case
            assessment.reviewer = request.user
            assessment.save()
            update_fields = ["updated_at"]
            for config in REVIEW_CONFIG.values():
                required = getattr(assessment, config["required_field"])
                setattr(use_case, config["required_field"], required)
                setattr(use_case, config["completed_field"], False)
                update_fields.extend(
                    [config["required_field"], config["completed_field"]]
                )
            use_case._history_user = request.user
            use_case.save(update_fields=update_fields)

            decision_assessment = use_case.decision_assessments.first()
            if decision_assessment is not None:
                decision_assessment.governance_precheck_completed = True
                decision_assessment.save(update_fields=["governance_precheck_completed"])

            messages.success(
                request,
                "Governance-Screening wurde gespeichert. "
                "Erforderliche Fachprüfungen sind neu geöffnet.",
            )
            return redirect(_next_url(use_case))
    else:
        form = GovernanceAssessmentForm()
    return render(
        request,
        "governance/form.html",
        {
            "form": form,
            "use_case": use_case,
            **_page_context(use_case, request.user),
        },
    )


@login_required
@transaction.atomic
def review_create(request, use_case_id, review_type):
    if not is_coordinator(request.user):
        raise PermissionDenied
    if review_type not in REVIEW_CONFIG:
        raise Http404

    use_case = get_object_or_404(UseCase, pk=use_case_id)
    screening = use_case.governance_assessments.first()
    if screening is None:
        messages.warning(
            request,
            "Vor einer Fachprüfung muss zuerst das Governance-Screening abgeschlossen werden.",
        )
        return redirect("governance:create", use_case_id=use_case.pk)

    config = REVIEW_CONFIG[review_type]
    required = getattr(screening, config["required_field"])
    latest_review = use_case.governance_reviews.filter(review_type=review_type).first()
    form = None

    if required:
        if request.method == "POST":
            form = GovernanceReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.use_case = use_case
                review.review_type = review_type
                review.reviewer = request.user
                review.save()
                setattr(use_case, config["completed_field"], review.is_completed)
                use_case._history_user = request.user
                use_case.save(update_fields=[config["completed_field"], "updated_at"])
                messages.success(
                    request,
                    f"{config['label']} wurde als eigenständiges Prüfartefakt gespeichert.",
                )
                return redirect(_next_url(use_case))
        else:
            form = GovernanceReviewForm()

    return render(
        request,
        "governance/review_form.html",
        {
            "use_case": use_case,
            "screening": screening,
            "review_type": review_type,
            "review_label": config["label"],
            "review_required": required,
            "latest_review": latest_review,
            "form": form,
            **_page_context(use_case, request.user),
        },
    )
