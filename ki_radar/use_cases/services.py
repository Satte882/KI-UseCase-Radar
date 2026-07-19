from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import UseCase

STATUS_ORDER = {
    UseCase.Status.IDEA: 0,
    UseCase.Status.REVIEW: 1,
    UseCase.Status.PILOT: 2,
    UseCase.Status.OPERATION: 3,
    UseCase.Status.ENDED: 4,
}


def required_fields_for_status(status: str) -> list[str]:
    requirements = {
        UseCase.Status.REVIEW: [
            "title",
            "problem_statement",
            "affected_process",
            "business_owner",
            "expected_benefit",
        ],
        UseCase.Status.PILOT: [
            "baseline",
            "success_criterion",
            "target_value",
            "data_sources",
            "next_review_date",
            "planned_pilot_end",
        ],
        UseCase.Status.OPERATION: [
            "realized_result",
            "business_owner",
            "technical_owner",
            "one_time_cost",
            "recurring_cost",
            "support_responsibility",
            "human_oversight",
            "next_review_date",
        ],
        UseCase.Status.ENDED: ["ending_reason", "data_and_access_handling"],
    }
    return requirements.get(status, [])


def validate_target_status(use_case: UseCase, target_status: str) -> None:
    missing = []
    for field_name in required_fields_for_status(target_status):
        value = getattr(use_case, field_name)
        if value in (None, ""):
            missing.append(use_case._meta.get_field(field_name).verbose_name)
    if target_status == UseCase.Status.PILOT and not use_case.governance_assessments.exists():
        missing.append("Governance-Screening")
    if target_status == UseCase.Status.OPERATION:
        checks = [
            (
                use_case.privacy_review_required,
                use_case.privacy_review_completed,
                "Datenschutzprüfung",
            ),
            (
                use_case.security_review_required,
                use_case.security_review_completed,
                "Informationssicherheitsprüfung",
            ),
            (use_case.legal_review_required, use_case.legal_review_completed, "Rechtsprüfung"),
        ]
        missing.extend(label for required, completed, label in checks if required and not completed)
    if missing:
        raise ValidationError("Für den Zielstatus fehlen: " + ", ".join(missing))


@transaction.atomic
def apply_status_transition(*, use_case: UseCase, target_status: str, actor) -> UseCase:
    validate_target_status(use_case, target_status)
    use_case.status = target_status
    if target_status == UseCase.Status.ENDED and not use_case.actual_end_date:
        use_case.actual_end_date = timezone.localdate()
    use_case.save()
    return use_case
