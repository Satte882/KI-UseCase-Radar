from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .models import UseCase


@dataclass(frozen=True)
class ReviewKind:
    key: str
    label: str
    required_field: str
    completed_field: str


@dataclass(frozen=True)
class GovernanceReviewStatus:
    kind: ReviewKind
    state: str
    label: str
    badge_class: str
    actor: str | None
    changed_at: date | datetime | None
    changed_at_has_time: bool
    attribution_note: str

    @property
    def editable(self) -> bool:
        return self.state in {"open", "completed"}


REVIEW_KINDS = (
    ReviewKind(
        key="privacy",
        label="Datenschutz",
        required_field="privacy_review_required",
        completed_field="privacy_review_completed",
    ),
    ReviewKind(
        key="security",
        label="Security",
        required_field="security_review_required",
        completed_field="security_review_completed",
    ),
    ReviewKind(
        key="legal",
        label="Recht",
        required_field="legal_review_required",
        completed_field="legal_review_completed",
    ),
)


def _display_name(user, *, fallback: str) -> str:
    if user is None:
        return fallback
    return user.get_display_name()


def _latest_completion_change(use_case: UseCase, field_name: str):
    records = list(
        use_case.history.select_related("history_user").order_by("history_date", "history_id")
    )
    latest_change = None
    previous_value = False
    for record in records:
        current_value = getattr(record, field_name)
        if current_value != previous_value:
            latest_change = record
        previous_value = current_value
    return latest_change


def build_governance_statuses(use_case: UseCase) -> tuple[GovernanceReviewStatus, ...]:
    assessment = None
    if use_case.pk:
        assessment = use_case.governance_assessments.select_related("reviewer").first()

    statuses = []
    for kind in REVIEW_KINDS:
        if assessment is None:
            statuses.append(
                GovernanceReviewStatus(
                    kind=kind,
                    state="not_assessed",
                    label="Noch nicht bewertet",
                    badge_class="text-bg-secondary",
                    actor=None,
                    changed_at=None,
                    changed_at_has_time=False,
                    attribution_note="Noch kein Governance-Screening vorhanden.",
                )
            )
            continue

        required = getattr(assessment, kind.required_field)
        completed = required and getattr(use_case, kind.completed_field)
        if not required:
            statuses.append(
                GovernanceReviewStatus(
                    kind=kind,
                    state="not_required",
                    label="Nicht erforderlich",
                    badge_class="text-bg-light border text-dark",
                    actor=_display_name(assessment.reviewer, fallback="unbekannt"),
                    changed_at=assessment.assessment_date,
                    changed_at_has_time=False,
                    attribution_note="Maßgebliches Governance-Screening",
                )
            )
            continue

        completion_change = _latest_completion_change(use_case, kind.completed_field)
        if completed:
            statuses.append(
                GovernanceReviewStatus(
                    kind=kind,
                    state="completed",
                    label="Abgeschlossen",
                    badge_class="text-bg-success",
                    actor=_display_name(
                        completion_change.history_user if completion_change else None,
                        fallback="System",
                    ),
                    changed_at=(
                        completion_change.history_date
                        if completion_change
                        else assessment.assessment_date
                    ),
                    changed_at_has_time=completion_change is not None,
                    attribution_note="Letzter Abschlussstatus",
                )
            )
            continue

        if (
            completion_change is not None
            and getattr(completion_change, kind.completed_field) is False
        ):
            statuses.append(
                GovernanceReviewStatus(
                    kind=kind,
                    state="open",
                    label="Offen",
                    badge_class="text-bg-warning",
                    actor=_display_name(completion_change.history_user, fallback="System"),
                    changed_at=completion_change.history_date,
                    changed_at_has_time=True,
                    attribution_note="Zuletzt wieder geöffnet",
                )
            )
            continue

        statuses.append(
            GovernanceReviewStatus(
                kind=kind,
                state="open",
                label="Offen",
                badge_class="text-bg-warning",
                actor=_display_name(assessment.reviewer, fallback="unbekannt"),
                changed_at=assessment.assessment_date,
                changed_at_has_time=False,
                attribution_note="Als erforderlich bewertet",
            )
        )
    return tuple(statuses)
