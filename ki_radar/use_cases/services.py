from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

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


@dataclass(frozen=True)
class DecisionCheck:
    target_status: str
    state: str
    title: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return not self.blockers

    @property
    def state_label(self) -> str:
        return {
            "ready": "Entscheidungsbereit",
            "blocked": "Blockiert",
            "review": "Prüfung empfohlen",
        }[self.state]


BASE_REQUIREMENTS = {
    UseCase.Status.REVIEW: [
        "title",
        "problem_statement",
        "affected_process",
        "business_owner",
        "expected_benefit",
    ],
    UseCase.Status.PILOT: [
        "data_sources",
        "next_review_date",
        "planned_pilot_end",
    ],
    UseCase.Status.OPERATION: [
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

PILOT_METRIC_REQUIREMENTS = [
    "metric_name",
    "metric_type",
    "metric_direction",
    "metric_unit",
    "metric_baseline",
    "metric_target",
    "metric_measurement_method",
]

GO_LIVE_METRIC_REQUIREMENTS = [
    "metric_actual",
    "metric_measurement_period",
    "metric_measured_at",
    "metric_evidence_url",
]

FIELD_LABELS = {
    "affected_process": "Betroffener Prozess",
    "business_owner": "Business Owner",
    "data_and_access_handling": "Umgang mit Daten und Zugaengen",
    "data_sources": "Datenquellen",
    "ending_reason": "Beendigungsgrund",
    "expected_benefit": "Erwarteter Nutzen",
    "human_oversight": "Menschliche Aufsicht",
    "next_review_date": "Nächster Entscheidungstermin",
    "one_time_cost": "Einmalige Kosten",
    "planned_pilot_end": "Geplantes Pilotende",
    "problem_statement": "Problemstellung",
    "recurring_cost": "Laufende Kosten",
    "support_responsibility": "Support-Verantwortung",
    "technical_owner": "Technischer Owner",
    "title": "Titel",
}


def required_fields_for_status(status: str) -> list[str]:
    return BASE_REQUIREMENTS.get(status, [])


def _combined_requirements(*groups: list[str]) -> list[str]:
    return list(dict.fromkeys(field_name for group in groups for field_name in group))


def _missing_fields(use_case: UseCase, field_names: list[str]) -> list[str]:
    missing = []
    for field_name in field_names:
        value = getattr(use_case, field_name)
        if value in (None, ""):
            missing.append(
                FIELD_LABELS.get(field_name, str(use_case._meta.get_field(field_name).verbose_name))
            )
    return missing


def check_pilot_start(use_case: UseCase) -> DecisionCheck:
    blockers = _missing_fields(
        use_case,
        _combined_requirements(
            BASE_REQUIREMENTS[UseCase.Status.REVIEW],
            BASE_REQUIREMENTS[UseCase.Status.PILOT],
            PILOT_METRIC_REQUIREMENTS,
        ),
    )
    warnings = []
    if not use_case.governance_assessments.exists():
        blockers.append("Governance-Screening")
    if (
        use_case.metric_baseline is not None
        and use_case.metric_target is not None
        and use_case.metric_baseline == use_case.metric_target
    ):
        warnings.append("Baseline und Zielwert sind identisch; die Nutzenhypothese prüfen.")
    if use_case.planned_pilot_end and use_case.planned_pilot_end < timezone.localdate():
        warnings.append("Das geplante Pilotende liegt bereits in der Vergangenheit.")
    state = "blocked" if blockers else ("review" if warnings else "ready")
    return DecisionCheck(
        target_status=UseCase.Status.PILOT,
        state=state,
        title="Pilot starten",
        blockers=blockers,
        warnings=warnings,
    )


def check_go_live(use_case: UseCase) -> DecisionCheck:
    blockers = _missing_fields(
        use_case,
        _combined_requirements(
            BASE_REQUIREMENTS[UseCase.Status.REVIEW],
            BASE_REQUIREMENTS[UseCase.Status.PILOT],
            PILOT_METRIC_REQUIREMENTS,
            BASE_REQUIREMENTS[UseCase.Status.OPERATION],
            GO_LIVE_METRIC_REQUIREMENTS,
        ),
    )
    warnings = []
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
    blockers.extend(label for required, completed, label in checks if required and not completed)
    if use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED:
        warnings.append(
            "Das Pilotziel wurde nicht erreicht. Ein Go-live benötigt eine ausdrückliche "
            "Begründung."
        )
    if use_case.planned_pilot_end and use_case.planned_pilot_end > timezone.localdate():
        warnings.append("Der geplante Pilotzeitraum ist noch nicht beendet.")
    state = "blocked" if blockers else ("review" if warnings else "ready")
    return DecisionCheck(
        target_status=UseCase.Status.OPERATION,
        state=state,
        title="Produktiv setzen",
        blockers=blockers,
        warnings=warnings,
    )


def decision_check_for_status(use_case: UseCase, target_status: str) -> DecisionCheck:
    if target_status == UseCase.Status.PILOT:
        return check_pilot_start(use_case)
    if target_status == UseCase.Status.OPERATION:
        return check_go_live(use_case)
    blockers = _missing_fields(use_case, BASE_REQUIREMENTS.get(target_status, []))
    return DecisionCheck(
        target_status=target_status,
        state="blocked" if blockers else "ready",
        title=UseCase.Status(target_status).label,
        blockers=blockers,
    )


def current_decision_check(use_case: UseCase) -> DecisionCheck:
    if use_case.status == UseCase.Status.IDEA:
        return decision_check_for_status(use_case, UseCase.Status.REVIEW)
    if use_case.status == UseCase.Status.REVIEW:
        return check_pilot_start(use_case)
    if use_case.status == UseCase.Status.PILOT:
        return check_go_live(use_case)
    if use_case.status == UseCase.Status.OPERATION:
        warnings = []
        today = timezone.localdate()
        if use_case.next_review_date and use_case.next_review_date < today:
            warnings.append("Die Betriebsüberprüfung ist überfällig.")
        if use_case.metric_measured_at and (today - use_case.metric_measured_at).days > 180:
            warnings.append("Die letzte Nutzenmessung ist älter als 180 Tage.")
        return DecisionCheck(
            target_status=UseCase.Status.OPERATION,
            state="review" if warnings else "ready",
            title="Betrieb fortführen",
            warnings=warnings,
        )
    return DecisionCheck(
        target_status=UseCase.Status.ENDED,
        state="ready",
        title="Abgeschlossen",
    )


def decision_due_date(use_case: UseCase) -> date | None:
    if use_case.status == UseCase.Status.PILOT:
        return use_case.planned_pilot_end or use_case.next_review_date
    return use_case.next_review_date


def decision_priority(use_case: UseCase) -> tuple[int, date, str]:
    today = timezone.localdate()
    check = current_decision_check(use_case)
    due = decision_due_date(use_case)
    if due and due < today:
        bucket = 0
    elif check.state == "blocked":
        bucket = 1
    elif due and due <= today + timedelta(days=30):
        bucket = 2
    elif check.state == "review":
        bucket = 3
    else:
        bucket = 4
    return bucket, due or date.max, use_case.short_id


def validate_target_status(use_case: UseCase, target_status: str) -> None:
    check = decision_check_for_status(use_case, target_status)
    if check.blockers:
        raise ValidationError("Für den Zielstatus fehlen: " + ", ".join(check.blockers))


@transaction.atomic
def apply_status_transition(*, use_case: UseCase, target_status: str, actor) -> UseCase:
    validate_target_status(use_case, target_status)
    use_case.status = target_status
    if target_status == UseCase.Status.ENDED and not use_case.actual_end_date:
        use_case.actual_end_date = timezone.localdate()
    use_case._history_user = actor
    use_case.save()
    return use_case
