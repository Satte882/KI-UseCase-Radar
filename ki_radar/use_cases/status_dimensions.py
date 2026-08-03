from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from .models import UseCase
from .services import approval_check, check_go_live, check_pilot_start, intake_blockers

if TYPE_CHECKING:
    from .journey import JourneyState


@dataclass(frozen=True)
class StatusDimension:
    key: str
    title: str
    label: str
    state: str
    explanation: str


@dataclass(frozen=True)
class UseCaseStatusDimensions:
    process: StatusDimension
    assessment: StatusDimension
    approval: StatusDimension
    measurement: StatusDimension
    lifecycle: StatusDimension
    next_lifecycle_decision: str

    @property
    def items(self) -> tuple[StatusDimension, ...]:
        return (
            self.process,
            self.assessment,
            self.approval,
            self.measurement,
            self.lifecycle,
        )


def _format_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _process_dimension(journey: JourneyState) -> StatusDimension:
    action = journey.next_action
    if action is not None:
        return StatusDimension(
            key="process",
            title="Arbeitsphase",
            label=action.label,
            state="blocked" if action.state == "blocked" else "review",
            explanation=action.reason or "Dieser Schritt ist als Nächstes zu bearbeiten.",
        )
    return StatusDimension(
        key="process",
        title="Arbeitsphase",
        label="Abgeschlossen",
        state="ready",
        explanation=journey.completion_message or "Für diesen Pfad ist kein weiterer Pflichtschritt offen.",
    )


def _assessment_dimension(use_case: UseCase) -> StatusDimension:
    assessment = use_case.decision_assessments.first()
    if assessment is not None:
        return StatusDimension(
            key="assessment",
            title="Assessment",
            label=f"Bewertung v{assessment.version} vorhanden",
            state="ready",
            explanation=(
                f"Confidence: {assessment.confidence_label}. "
                "Eine neue Version ersetzt die bestehende Bewertung nicht rückwirkend."
            ),
        )

    blockers = intake_blockers(use_case)
    if blockers:
        return StatusDimension(
            key="assessment",
            title="Assessment",
            label="Bewertung blockiert",
            state="blocked",
            explanation=f"Vor der Bewertung fehlt: {blockers[0]}.",
        )
    return StatusDimension(
        key="assessment",
        title="Assessment",
        label="Bewertungsbereit",
        state="review",
        explanation="Der Intake ist vollständig; eine strukturierte Bewertung steht noch aus.",
    )


def _approval_dimension(use_case: UseCase) -> StatusDimension:
    final_decision = use_case.approval_decisions.filter(finalized_at__isnull=False).first()
    if final_decision is not None:
        positive = final_decision.decision_status in {
            UseCase.DecisionStatus.APPROVED,
            UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS,
        }
        return StatusDimension(
            key="approval",
            title="Freigabe",
            label=final_decision.get_decision_status_display(),
            state="ready" if positive else "blocked",
            explanation="Die verbindliche Entscheidung ist versioniert und abgeschlossen.",
        )

    pending = use_case.approval_decisions.filter(finalized_at__isnull=True).first()
    if pending is not None:
        return StatusDimension(
            key="approval",
            title="Freigabe",
            label="Zweitfreigabe offen",
            state="blocked",
            explanation="Die vorgeschlagene Freigabe ist noch nicht final bestätigt.",
        )

    assessment = use_case.decision_assessments.first()
    if assessment is None:
        return StatusDimension(
            key="approval",
            title="Freigabe",
            label="Bewertung erforderlich",
            state="review",
            explanation="Eine Freigabeentscheidung ist erst nach einer strukturierten Bewertung möglich.",
        )

    check = approval_check(
        use_case=use_case,
        target_status=assessment.recommendation,
        governance_confirmed=True,
    )
    if use_case.coordinator_id is None:
        check.blockers.append("KI-Koordination nicht zugewiesen")
    if check.blockers:
        return StatusDimension(
            key="approval",
            title="Freigabe",
            label="Freigabe blockiert",
            state="blocked",
            explanation=f"Nächster offener Punkt: {check.blockers[0]}.",
        )
    return StatusDimension(
        key="approval",
        title="Freigabe",
        label="Entscheidungsbereit",
        state="ready",
        explanation="Bewertung und fachliche Voraussetzungen liegen für die Entscheidung vor.",
    )


def _measurement_dimension(use_case: UseCase) -> StatusDimension:
    result = use_case.metric_result
    state = {
        UseCase.MetricResult.ACHIEVED: "ready",
        UseCase.MetricResult.NOT_ACHIEVED: "blocked",
        UseCase.MetricResult.NOT_MEASURED: "review",
        UseCase.MetricResult.NOT_DEFINED: "blocked",
    }[result]
    explanations = {
        UseCase.MetricResult.ACHIEVED: "Der gemessene Ist-Wert erfüllt das definierte Ziel.",
        UseCase.MetricResult.NOT_ACHIEVED: "Der gemessene Ist-Wert verfehlt das definierte Ziel.",
        UseCase.MetricResult.NOT_MEASURED: "Ziel und Messlogik sind definiert; ein Ist-Wert fehlt.",
        UseCase.MetricResult.NOT_DEFINED: "Eine vollständige Erfolgsmetrik ist noch nicht definiert.",
    }
    return StatusDimension(
        key="measurement",
        title="Messung",
        label=use_case.metric_result_label,
        state=state,
        explanation=explanations[result],
    )


def _lifecycle_dimension(use_case: UseCase) -> StatusDimension:
    state = {
        UseCase.Status.IDEA: "review",
        UseCase.Status.REVIEW: "review",
        UseCase.Status.PILOT: "review",
        UseCase.Status.OPERATION: "ready",
        UseCase.Status.ENDED: "ready",
    }[use_case.status]
    explanations = {
        UseCase.Status.IDEA: "Der Use Case befindet sich in Erfassung und fachlicher Klärung.",
        UseCase.Status.REVIEW: "Bewertung, Freigabe und Übergabe werden vorbereitet.",
        UseCase.Status.PILOT: "Der Use Case wird unter definierten Pilotbedingungen erprobt.",
        UseCase.Status.OPERATION: "Der Use Case befindet sich im geregelten Betrieb.",
        UseCase.Status.ENDED: "Der Lifecycle ist beendet; Abschluss und Datenbehandlung bleiben nachvollziehbar.",
    }
    return StatusDimension(
        key="lifecycle",
        title="Lifecycle",
        label=use_case.get_status_display(),
        state=state,
        explanation=explanations[use_case.status],
    )


def _next_lifecycle_decision(use_case: UseCase) -> str:
    if use_case.status == UseCase.Status.IDEA:
        blockers = intake_blockers(use_case)
        if blockers:
            return f"Vor der Bewertung fehlt: {blockers[0]}."
        return "Nächste Aktion: strukturierte Bewertung anlegen."

    if use_case.status == UseCase.Status.REVIEW:
        check = check_pilot_start(use_case)
        if check.blockers:
            return f"Pilotstart blockiert: {check.blockers[0]}."
        return "Nächste Aktion: tatsächlichen Pilotstart bestätigen."

    if use_case.status == UseCase.Status.PILOT:
        check = check_go_live(use_case)
        if check.blockers:
            return f"Go-live blockiert: {check.blockers[0]}."
        if use_case.planned_pilot_end:
            return f"Go-live-Entscheidung zum geplanten Pilotende am {_format_date(use_case.planned_pilot_end)}."
        return "Für die Go-live-Entscheidung fehlt das geplante Pilotende."

    if use_case.status == UseCase.Status.OPERATION:
        if use_case.next_review_date:
            return f"Nächste Betriebsentscheidung am {_format_date(use_case.next_review_date)}."
        return "Für den Betrieb fehlt der nächste Entscheidungstermin."

    return "Keine weitere Lifecycle-Entscheidung vorgesehen."


def build_use_case_status_dimensions(
    use_case: UseCase,
    journey: JourneyState,
) -> UseCaseStatusDimensions:
    return UseCaseStatusDimensions(
        process=_process_dimension(journey),
        assessment=_assessment_dimension(use_case),
        approval=_approval_dimension(use_case),
        measurement=_measurement_dimension(use_case),
        lifecycle=_lifecycle_dimension(use_case),
        next_lifecycle_decision=_next_lifecycle_decision(use_case),
    )
