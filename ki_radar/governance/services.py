from dataclasses import dataclass

from django.db import transaction

from ki_radar.use_cases.models import UseCase

from .models import GovernanceAssessment, GovernanceReview


@dataclass(frozen=True)
class ReviewDefinition:
    review_type: str
    label: str
    responsible_role: str
    required_field: str
    completed_field: str
    rationale_field: str


REVIEW_DEFINITIONS = {
    GovernanceReview.ReviewType.PRIVACY: ReviewDefinition(
        review_type=GovernanceReview.ReviewType.PRIVACY,
        label="Datenschutzprüfung",
        responsible_role="Datenschutz",
        required_field="privacy_review_required",
        completed_field="privacy_review_completed",
        rationale_field="privacy_review_rationale",
    ),
    GovernanceReview.ReviewType.SECURITY: ReviewDefinition(
        review_type=GovernanceReview.ReviewType.SECURITY,
        label="Informationssicherheitsprüfung",
        responsible_role="Informationssicherheit",
        required_field="security_review_required",
        completed_field="security_review_completed",
        rationale_field="security_review_rationale",
    ),
    GovernanceReview.ReviewType.LEGAL: ReviewDefinition(
        review_type=GovernanceReview.ReviewType.LEGAL,
        label="Rechtsprüfung",
        responsible_role="Recht / Compliance",
        required_field="legal_review_required",
        completed_field="legal_review_completed",
        rationale_field="legal_review_rationale",
    ),
}
REVIEW_ORDER = tuple(REVIEW_DEFINITIONS)


def review_definition(review_type: str) -> ReviewDefinition:
    return REVIEW_DEFINITIONS[review_type]


def latest_review_for_screening(
    *,
    use_case: UseCase,
    review_type: str,
    screening: GovernanceAssessment,
) -> GovernanceReview | None:
    return (
        use_case.governance_reviews.filter(
            review_type=review_type,
            screening=screening,
        )
        .select_related("reviewer", "screening")
        .first()
    )


def review_history(*, use_case: UseCase, review_type: str):
    return use_case.governance_reviews.filter(review_type=review_type).select_related(
        "reviewer", "screening"
    )


@transaction.atomic
def create_screening_review_artifacts(
    *,
    assessment: GovernanceAssessment,
    actor,
) -> tuple[GovernanceReview, ...]:
    """Create one explicit formal-review status artifact per review type and screening."""
    artifacts = []
    for definition in REVIEW_DEFINITIONS.values():
        required = getattr(assessment, definition.required_field)
        artifact = GovernanceReview(
            use_case=assessment.use_case,
            screening=assessment,
            review_type=definition.review_type,
            status=(
                GovernanceReview.Status.OPEN if required else GovernanceReview.Status.NOT_RELEVANT
            ),
            reviewed_at=assessment.assessment_date,
            reviewer=actor,
            responsible_role=definition.responsible_role,
            result="",
            rationale=assessment.review_rationale(definition.review_type),
        )
        artifact.full_clean()
        artifact._history_user = actor
        artifact.save()
        artifacts.append(artifact)
    return tuple(artifacts)


def sync_completion_from_review(
    *,
    use_case: UseCase,
    review: GovernanceReview,
    actor,
) -> None:
    definition = review_definition(review.review_type)
    setattr(use_case, definition.completed_field, review.is_completed)
    use_case._history_user = actor
    use_case.save(update_fields=[definition.completed_field, "updated_at"])
