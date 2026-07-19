from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.accounts.permissions import is_coordinator
from ki_radar.use_cases.models import UseCase

from .forms import GovernanceAssessmentForm


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
            use_case.privacy_review_required = assessment.privacy_review_required
            use_case.security_review_required = assessment.security_review_required
            use_case.legal_review_required = assessment.legal_review_required
            use_case.save(
                update_fields=[
                    "privacy_review_required",
                    "security_review_required",
                    "legal_review_required",
                    "updated_at",
                ]
            )
            messages.success(request, "Governance-Screening wurde gespeichert.")
            return redirect(use_case)
    else:
        form = GovernanceAssessmentForm()
    return render(request, "governance/form.html", {"form": form, "use_case": use_case})
