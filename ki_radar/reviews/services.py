from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from ki_radar.use_cases import services as use_case_services
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.permissions import (
    can_confirm_early_go_live_exception,
    can_confirm_go_live_exception,
)
from ki_radar.use_cases.scale_readiness import (
    SCALE_READINESS_SCHEMA_VERSION,
    build_scale_readiness_snapshot,
    evaluate_scale_readiness,
    extract_scale_evidence,
)

from .models import EarlyGoLiveException, Review

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
EARLY_EXCEPTION_FIELDS = (
    "early_go_live_exception_confirmed",
    "early_go_live_original_pilot_end",
    "early_go_live_evidence_basis",
    "early_go_live_unobserved_risks",
    "early_go_live_mitigation_measures",
)
SCALE_SNAPSHOT_DECISIONS = {
    Review.Decision.GO_LIVE,
    Review.Decision.CONTINUE,
    Review.Decision.REWORK,
    Review.Decision.END,
}


def _early_go_live_required(use_case: UseCase, decision: str | None) -> bool:
    return bool(
        decision == Review.Decision.GO_LIVE
        and use_case.planned_pilot_end
        and use_case.planned_pilot_end > timezone.localdate()
    )


def _validate_review_transition(*, use_case: UseCase, actor, review_data: dict) -> None:
    decision = review_data.get("decision")
    target_status = review_data.get("new_status")
    expected_status = DECISION_TARGETS.get(decision)

    if expected_status and target_status != expected_status:
        raise ValidationError(
            f"Die Entscheidung {Review.Decision(decision).label} erfordert den Status "
            f"{UseCase.Status(expected_status).label}."
        )

    status_must_stay = decision in {
        Review.Decision.PAUSE,
        Review.Decision.REWORK,
        Review.Decision.CONTINUE,
    }
    if status_must_stay and target_status != use_case.status:
        raise ValidationError(
            "Fortführen, Pausieren und Überarbeiten dürfen den Lifecycle-Status nicht ändern."
        )

    invalid_return = decision == Review.Decision.RETURN and (
        not target_status or STATUS_ORDER[target_status] >= STATUS_ORDER[use_case.status]
    )
    if invalid_return:
        raise ValidationError("Eine Rückstufung erfordert eine frühere Lifecycle-Phase.")

    if decision == Review.Decision.GO_LIVE and use_case.status != UseCase.Status.PILOT:
        raise ValidationError("Ein Go-live ist ausschließlich aus dem Status Pilot möglich.")

    exception_required = (
        decision == Review.Decision.GO_LIVE
        and use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED
    )
    if exception_required and not review_data.get("go_live_exception_confirmed"):
        raise ValidationError(
            "Ein Go-live bei verfehltem Pilotziel benötigt eine ausdrücklich bestätigte Ausnahme."
        )
    if exception_required and not can_confirm_go_live_exception(actor):
        raise PermissionDenied(
            "Nur ein Mitglied der Gruppe KI-Koordinator darf eine Go-live-Ausnahme bestätigen."
        )
    if exception_required and not str(review_data.get("rationale", "")).strip():
        raise ValidationError(
            "Die Go-live-Ausnahme benötigt eine konkrete Entscheidungsbegründung."
        )
    if not exception_required:
        review_data["go_live_exception_confirmed"] = False

    early_exception_required = _early_go_live_required(use_case, decision)
    if early_exception_required:
        if not review_data.get("early_go_live_exception_confirmed"):
            raise ValidationError(
                "Eine Produktivsetzung vor dem geplanten Pilotende benötigt eine ausdrücklich "
                "bestätigte Ausnahme."
            )
        if not can_confirm_early_go_live_exception(actor):
            raise PermissionDenied(
                "Nur ein Mitglied der Gruppe KI-Koordinator darf eine vorzeitige "
                "Produktivsetzung bestätigen."
            )
        missing = [
            label
            for field_name, label in [
                ("rationale", "Entscheidungsbegründung"),
                ("early_go_live_evidence_basis", "Mess- und Evidenzbasis"),
                ("early_go_live_unobserved_risks", "Nicht vollständig beobachtete Risiken"),
                ("early_go_live_mitigation_measures", "Maßnahmen zur Risikobegrenzung"),
            ]
            if not str(review_data.get(field_name, "")).strip()
        ]
        if missing:
            raise ValidationError(
                "Für die vorzeitige Produktivsetzung fehlen: " + ", ".join(missing)
            )
        review_data["early_go_live_original_pilot_end"] = use_case.planned_pilot_end
    else:
        for field_name in EARLY_EXCEPTION_FIELDS:
            review_data[field_name] = False if field_name.endswith("confirmed") else ""
        review_data["early_go_live_original_pilot_end"] = None

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


def _validate_scale_decision(
    *,
    use_case: UseCase,
    review_data: dict,
    scale_evidence: dict,
):
    decision = review_data.get("decision")
    if use_case.status != UseCase.Status.PILOT or decision not in SCALE_SNAPSHOT_DECISIONS:
        return None

    result = evaluate_scale_readiness(use_case, scale_evidence)
    if decision == Review.Decision.GO_LIVE:
        if result.blockers:
            raise ValidationError(
                "Scale Readiness blockiert: "
                + "; ".join(finding.message for finding in result.blockers)
            )
        if result.state == "conditional":
            missing = [
                label
                for field_name, label in (
                    ("open_actions", "Kompensationsmaßnahme"),
                    ("action_owner", "Maßnahmenverantwortliche Person"),
                    ("action_due_date", "Fälligkeitsdatum der Maßnahme"),
                )
                if not review_data.get(field_name)
            ]
            if missing:
                raise ValidationError("Conditional Go benötigt: " + ", ".join(missing))
    return result


@transaction.atomic
def create_review(*, use_case, actor, data) -> Review:
    use_case = UseCase.objects.select_for_update().get(pk=use_case.pk)
    previous_status = use_case.status
    review_data = data.copy()
    pilot_start = review_data.pop("pilot_start", None)
    scale_evidence = extract_scale_evidence(review_data)

    _validate_review_transition(use_case=use_case, actor=actor, review_data=review_data)
    scale_result = _validate_scale_decision(
        use_case=use_case,
        review_data=review_data,
        scale_evidence=scale_evidence,
    )

    early_exception_required = _early_go_live_required(use_case, review_data.get("decision"))
    early_exception_data = {
        field_name: review_data.pop(field_name, None) for field_name in EARLY_EXCEPTION_FIELDS
    }

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
        use_case_services.apply_status_transition(
            use_case=use_case,
            target_status=target_status,
            actor=actor,
            pilot_start=pilot_start,
            allow_early_go_live_exception=early_exception_required,
            scale_evidence=(scale_evidence if target_status == UseCase.Status.OPERATION else None),
        )
    else:
        use_case._history_user = actor
        use_case.save()

    snapshot = {}
    if scale_result is not None:
        snapshot = build_scale_readiness_snapshot(use_case, scale_evidence, scale_result)

    review = Review(
        use_case=use_case,
        reviewer=actor,
        previous_status=previous_status,
        scale_readiness_schema_version=SCALE_READINESS_SCHEMA_VERSION,
        scale_readiness_snapshot=snapshot,
        **review_data,
    )
    review._history_user = actor
    review.save()

    if early_exception_required:
        EarlyGoLiveException.objects.create(
            review=review,
            original_planned_pilot_end=early_exception_data["early_go_live_original_pilot_end"],
            decision_date=review.review_date,
            reason=review.rationale,
            evidence_basis=early_exception_data["early_go_live_evidence_basis"],
            unobserved_risks=early_exception_data["early_go_live_unobserved_risks"],
            mitigation_measures=early_exception_data["early_go_live_mitigation_measures"],
            confirmed_by=actor,
            confirmed_by_label=actor.get_display_name(),
            confirmed_role="KI-Koordinator",
        )
    return review
