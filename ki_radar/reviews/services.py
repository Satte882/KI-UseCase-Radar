from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.permissions import can_confirm_go_live_exception
from ki_radar.use_cases.services import apply_status_transition

from .models import Review


DECISION_TARGETS = {
    Review.Decision.START_REVIEW: UseCase.Status.REVIEW,
    Review.Decision.START_PILOT: UseCase.Status.PILOT,
    Review.Decision.GO_LIVE: UseCase.Status.OPERATION,
    Review.Decision.END: UseCase.Status.ENDED,
}
STATUS_ORDER = {
    UseCase.Status.IDEA: 0,
    UseCase.Status.REVIEW: 1,
    UseCase.Status.PILOT: 2,
    UseCase.Status.OPERATION: 3,
    UseCase.Status.ENDED: 4,
}


def _validate_review_transition(*, use_case: UseCase, actor, review_data: dict) -> None:
    decision = review_data.get("decision")
    target_status = review_data.get("new_status")
    expected_status = DECISION_TARGETS.get(decision)

    if expected_status and target_status != expected_status:
        raise ValidationError(
            f"Die Entscheidung {Review.Decision(decision).label} erfordert den Status "
            f"{UseCase.Status(expected_status).label}."
        )

    if decision in {Review.Decision.PAUSE, Review.Decision.REWORK, Review.Decision.CONTINUE}:
        if target_status != use_case.status:
            raise ValidationError(
                "Fortführen, Pausieren und Überarbeiten dürfen den Lifecycle-Status nicht ändern."
            )

    if decision == Review.Decision.RETURN:
        if not target_status or STATUS_ORDER[target_status] >= STATUS_ORDER[use_case.status]:
            raise ValidationError("Eine Rückstufung erfordert eine frühere Lifecycle-Phase.")

    if decision == Review.Decision.GO_LIVE:
        if use_case.status != UseCase.Status.PILOT:
            raise ValidationError("Ein Go-live ist ausschließlich aus dem Status Pilot möglich.")
        exception_required = use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED
        if exception_required:
            if not review_data.get("go_live_exception_confirmed"):
                raise ValidationError(
                    "Ein Go-live bei verfehltem Pilotziel benötigt eine ausdrücklich bestätigte "
                    "Ausnahme."
                )
            if not can_confirm_go_live_exception(actor):
                raise PermissionDenied(
                    "Nur ein Mitglied der Gruppe KI-Koordinator darf eine Go-live-Ausnahme "
                    "bestätigen."
                )
            if not str(review_data.get("rationale", "")).strip():
                raise ValidationError(
                    "Die Go-live-Ausnahme benötigt eine konkrete Entscheidungsbegründung."
                )
        else:
            review_data["go_live_exception_confirmed"] = False
    else:
        review_data["go_live_exception_confirmed"] = False

    if decision == Review.Decision.END:
        missing = [
            label
            for field_name, label in [
                ("ending_reason", "Beendigungsgrund"),
                ("data_and_access_handling", "Umgang mit Daten und Zugängen"),
            ]
            if not str(review_data.get(field_name, "")).strip()
        ]
        if missing:
            raise ValidationError("Für den Abschluss fehlen: " + ", ".join(missing))


@transaction.atomic
def create_review(*, use_case, actor, data) -> Review:
    use_case = UseCase.objects.select_for_update().get(pk=use_case.pk)
    previous_status = use_case.status
    review_data = data.copy()
    pilot_start = review_data.pop("pilot_start", None)

    _validate_review_transition(use_case=use_case, actor=actor, review_data=review_data)

    for field in [
        "ending_reason",
        "data_and_access_handling",
        "replacement_solution",
        "final_assessment",
        "lessons_learned",
    ]:
        value = review_data.pop(field, "")
        if value:
            setattr(use_case, field, value)

    use_case.next_review_date = review_data.get("next_review_date")
    target_status = review_data["new_status"]

    if target_status != previous_status:
        apply_status_transition(
            use_case=use_case,
            target_status=target_status,
            actor=actor,
            pilot_start=pilot_start,
        )
    else:
        use_case._history_user = actor
        use_case.save()

    review = Review(
        use_case=use_case,
        reviewer=actor,
        previous_status=previous_status,
        **review_data,
    )
    review._history_user = actor
    review.save()
    return review
