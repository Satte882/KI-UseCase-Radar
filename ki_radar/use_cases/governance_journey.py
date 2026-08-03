from __future__ import annotations

from django.urls import reverse

from ki_radar.accounts.permissions import is_coordinator

from . import journey as legacy
from . import workflow
from .models import UseCase

JourneyState = workflow.JourneyState
JourneyStep = workflow.JourneyStep

REVIEW_ORDER = (
    ("privacy", "Datenschutzprüfung", "privacy_review_required", "privacy_review_completed"),
    (
        "security",
        "Informationssicherheitsprüfung",
        "security_review_required",
        "security_review_completed",
    ),
    ("legal", "Rechtsprüfung", "legal_review_required", "legal_review_completed"),
)

_original_build_use_case = None


def _state(journey: JourneyState, steps: list[JourneyStep]) -> JourneyState:
    return JourneyState(
        path_label=journey.path_label,
        steps=tuple(steps),
        next_action=next(
            (step for step in steps if step.state in {"current", "blocked"}),
            None,
        ),
        completion_message=journey.completion_message,
    )


def _governance_step(use_case: UseCase, user) -> JourneyStep:
    final_decision = use_case.approval_decisions.filter(finalized_at__isnull=False).first()
    if final_decision is not None:
        if final_decision.decision_status in {
            UseCase.DecisionStatus.DEFERRED,
            UseCase.DecisionStatus.NOT_PURSUED,
        }:
            return JourneyStep(
                key="governance",
                label="Governance",
                state="optional",
                reason="Für die finale negative Entscheidung ist keine positive Freigabeprüfung erforderlich.",
            )
        return JourneyStep(
            key="governance",
            label="Governance",
            state="complete",
            url=f"{use_case.get_absolute_url()}#governance",
            action_label="Governance öffnen",
            reason="Der Governance-Pfad wurde vor der finalen positiven Freigabe abgeschlossen.",
        )

    assessment = use_case.decision_assessments.first()
    if assessment is None:
        return JourneyStep(
            key="governance",
            label="Governance",
            state="upcoming",
            reason="Das Governance-Screening folgt nach der strukturierten Bewertung.",
        )

    screening = use_case.governance_assessments.first()
    if screening is None:
        allowed = is_coordinator(user)
        return JourneyStep(
            key="governance",
            label="Governance",
            state="current",
            url=(
                reverse("governance:create", kwargs={"use_case_id": use_case.pk})
                if allowed
                else None
            ),
            action_label="Governance-Screening durchführen" if allowed else "",
            reason=(
                "Die Bewertung liegt vor; nun müssen die erforderlichen Governance-Prüfungen "
                "aus einem Screening abgeleitet werden."
            ),
        )

    incomplete_reviews = [
        (review_type, label)
        for review_type, label, required_field, completed_field in REVIEW_ORDER
        if getattr(screening, required_field) and not getattr(use_case, completed_field)
    ]
    if incomplete_reviews:
        review_type, label = incomplete_reviews[0]
        allowed = is_coordinator(user)
        return JourneyStep(
            key="governance",
            label="Governance",
            state="blocked",
            url=(
                reverse(
                    "governance:review",
                    kwargs={"use_case_id": use_case.pk, "review_type": review_type},
                )
                if allowed
                else None
            ),
            action_label=f"{label} durchführen" if allowed else "",
            reason="Das Governance-Screening ist vorhanden; erforderliche Fachprüfungen sind offen.",
            details=tuple(item_label for _item_type, item_label in incomplete_reviews),
        )

    required_reviews = [
        label
        for _review_type, label, required_field, _completed_field in REVIEW_ORDER
        if getattr(screening, required_field)
    ]
    reason = (
        "Governance-Screening und alle erforderlichen Fachprüfungen sind abgeschlossen."
        if required_reviews
        else "Das Governance-Screening hat keine zusätzlichen Fachprüfungen abgeleitet."
    )
    return JourneyStep(
        key="governance",
        label="Governance",
        state="complete",
        url=f"{use_case.get_absolute_url()}#governance",
        action_label="Governance öffnen",
        reason=reason,
    )


def _insert_governance(
    use_case: UseCase,
    user,
    journey: JourneyState,
) -> JourneyState:
    governance_step = _governance_step(use_case, user)
    steps: list[JourneyStep] = []
    inserted = False

    for step in journey.steps:
        if step.key == "approval" and not inserted:
            steps.append(governance_step)
            inserted = True

        if (
            step.key == "approval"
            and step.state == "current"
            and governance_step.state in {"current", "blocked"}
        ):
            steps.append(
                JourneyStep(
                    key="approval",
                    label=step.label,
                    state="upcoming",
                    reason="Die Freigabe folgt nach dem abgeschlossenen Governance-Pfad.",
                )
            )
        else:
            steps.append(step)

    if not inserted:
        steps.append(governance_step)

    return _state(journey, steps)


def build_use_case_journey(use_case: UseCase, user) -> JourneyState:
    if _original_build_use_case is None:
        raise RuntimeError("Governance journey is not installed.")
    journey = _original_build_use_case(use_case, user)
    return _insert_governance(use_case, user, journey)


def install() -> None:
    global _original_build_use_case
    _original_build_use_case = workflow.build_use_case_journey
    workflow.build_use_case_journey = build_use_case_journey
    legacy.build_use_case_journey = build_use_case_journey
