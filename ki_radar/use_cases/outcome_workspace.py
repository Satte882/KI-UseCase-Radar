from __future__ import annotations

from urllib.parse import urlencode

from django.urls import reverse

from ki_radar.delivery.models import DeliveryPackage
from ki_radar.delivery.services import current_delivery_package, current_handed_over_package

from .models import UseCase
from .permissions import can_start_pilot
from .services import check_pilot_start
from .workflow import (
    JourneyState,
    JourneyStep,
    _state,
    build_use_case_journey,
    pilot_start_url,
)

OUTCOME_STAGES = (
    ("pilot", "Pilot", "pilot"),
    ("effect", "Wirkung", "measurement"),
    ("decision", "Ergebnisentscheidung", "outcome_decision"),
    ("operation", "Betrieb", "operation"),
    ("closure", "Abschluss", "closure"),
)
OUTCOME_STAGE_KEYS = {stage for stage, _label, _step_key in OUTCOME_STAGES}


def normalize_outcome_stage(value: str | None) -> str:
    return value if value in OUTCOME_STAGE_KEYS else "pilot"


def outcome_workspace_url(
    stage: str,
    *,
    use_case: UseCase | None = None,
) -> str:
    query = {"stage": normalize_outcome_stage(stage)}
    if use_case is not None:
        query["use_case"] = str(use_case.pk)
    return f"{reverse('reporting:outcome_workspace')}?{urlencode(query)}"


def _handover_step(package: DeliveryPackage | None) -> JourneyStep:
    if package is None:
        return JourneyStep(
            key="handover",
            label="Übergabe",
            state="upcoming",
            reason="Die verbindliche Übergabe beginnt nach einem vollständigen Delivery Package.",
        )
    if package.status == DeliveryPackage.Status.HANDED_OVER and package.handed_over_at:
        return JourneyStep(
            key="handover",
            label="Übergabe",
            state="complete",
            url=package.get_absolute_url(),
            action_label="Übergabe öffnen",
            reason=f"Delivery Package v{package.version} wurde verbindlich übergeben.",
        )
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        return JourneyStep(
            key="handover",
            label="Übergabe",
            state="blocked",
            url=package.get_absolute_url(),
            action_label="Übergabe prüfen",
            reason="Der Übergabestatus besitzt keinen verbindlichen Übergabezeitpunkt.",
        )
    return JourneyStep(
        key="handover",
        label="Übergabe",
        state="current" if package.status == DeliveryPackage.Status.READY else "blocked",
        url=package.get_absolute_url(),
        action_label="Delivery Package öffnen",
        reason=(
            "Das Package ist bereit; die Übergabe an das externe Delivery-System steht aus."
            if package.status == DeliveryPackage.Status.READY
            else "Das Delivery Package muss vor der Übergabe vervollständigt werden."
        ),
    )


def _pilot_step(
    use_case: UseCase,
    *,
    handed_over: bool,
    user,
) -> JourneyStep:
    url = outcome_workspace_url("pilot", use_case=use_case)
    if not handed_over:
        return JourneyStep(
            key="pilot",
            label="Pilot",
            state="upcoming",
            reason="Die Pilotbeobachtung beginnt erst nach der verbindlichen Übergabe.",
        )
    if use_case.status == UseCase.Status.PILOT:
        return JourneyStep(
            key="pilot",
            label="Pilot",
            state="current",
            url=url,
            action_label="Pilotübersicht öffnen",
            reason=(
                "Der Pilot läuft im externen Delivery-System; KI-Radar hält den Review-Snapshot."
            ),
        )
    if (
        use_case.status in {UseCase.Status.OPERATION, UseCase.Status.ENDED}
        or use_case.actual_end_date
    ):
        return JourneyStep(
            key="pilot",
            label="Pilot",
            state="complete",
            url=url,
            action_label="Pilotübersicht öffnen",
            reason=(
                "Der Pilot ist fachlich abgeschlossen oder das Vorhaben befindet sich "
                "bereits im Betrieb."
            ),
        )
    check = check_pilot_start(use_case)
    allowed = can_start_pilot(user, use_case)
    reason = "Die Übergabe ist erfolgt; der tatsächliche Pilotbeginn muss bestätigt werden."
    if not allowed:
        reason += " Nur ein KI-Koordinator oder der zuständige Business Owner darf starten."
    return JourneyStep(
        key="pilot",
        label="Pilot",
        state="blocked" if check.blockers else "current",
        url=pilot_start_url(use_case) if allowed else None,
        action_label="Pilot starten" if allowed else "",
        reason=reason,
        details=tuple(check.blockers),
    )


def _measurement_step(
    use_case: UseCase,
    *,
    handed_over: bool,
) -> JourneyStep:
    url = reverse("use_cases:edit", kwargs={"pk": use_case.pk})
    if use_case.metric_actual is not None and use_case.metric_evidence_url:
        return JourneyStep(
            key="measurement",
            label="Wirkungsmessung",
            state="complete",
            url=outcome_workspace_url("effect", use_case=use_case),
            action_label="Wirkung öffnen",
            reason=f"{use_case.metric_result_label}; Messwert und Nachweis liegen vor.",
        )
    if use_case.metric_actual is not None:
        return JourneyStep(
            key="measurement",
            label="Wirkungsmessung",
            state="blocked",
            url=f"{url}?highlight=metric_evidence_url",
            action_label="Messnachweis ergänzen",
            reason="Ein Ist-Wert ist erfasst, aber der verbindliche Messnachweis fehlt.",
            details=("Messnachweis",),
        )
    if not handed_over:
        return JourneyStep(
            key="measurement",
            label="Wirkungsmessung",
            state="upcoming",
            reason="Die Wirkungsmessung folgt nach Übergabe und Pilotdurchführung.",
        )
    pilot_active = use_case.status == UseCase.Status.PILOT
    return JourneyStep(
        key="measurement",
        label="Wirkungsmessung",
        state="current" if pilot_active else "upcoming",
        url=f"{url}?highlight=metric_actual" if pilot_active else None,
        action_label="Ist-Wert erfassen" if pilot_active else "",
        reason=(
            "Baseline, Ziel, Ist-Wert und Messnachweis werden zum Review manuell "
            "in KI-Radar bestätigt."
            if pilot_active
            else "Die Messung wird zum vereinbarten Review-Zeitpunkt dokumentiert."
        ),
    )


def _outcome_decision_step(
    use_case: UseCase,
    *,
    measurement_complete: bool,
) -> JourneyStep:
    if not measurement_complete:
        return JourneyStep(
            key="outcome_decision",
            label="Ergebnisentscheidung",
            state="upcoming",
            reason="Eine belastbare Folgeentscheidung setzt Messwert und Nachweis voraus.",
        )
    if use_case.status in {UseCase.Status.OPERATION, UseCase.Status.ENDED}:
        return JourneyStep(
            key="outcome_decision",
            label="Ergebnisentscheidung",
            state="complete",
            url=outcome_workspace_url("decision", use_case=use_case),
            action_label="Entscheidungsrahmen öffnen",
            reason=(
                "Der Lifecycle-Status zeigt bereits Betrieb oder Abschluss; das versionierte "
                "Review-Artefakt folgt in einem separaten Inkrement."
            ),
        )
    return JourneyStep(
        key="outcome_decision",
        label="Ergebnisentscheidung",
        state="current",
        url=outcome_workspace_url("decision", use_case=use_case),
        action_label="Entscheidungsrahmen prüfen",
        reason=("Scale-, Continue- oder Stop-Entscheidung wird noch nicht gespeichert."),
    )


def _operation_step(use_case: UseCase) -> JourneyStep:
    url = outcome_workspace_url("operation", use_case=use_case)
    if use_case.status == UseCase.Status.ENDED:
        return JourneyStep(
            key="operation",
            label="Betrieb",
            state="complete",
            url=url,
            action_label="Betriebskontext öffnen",
            reason="Der produktive Betrieb ist beendet.",
        )
    if use_case.status == UseCase.Status.OPERATION:
        return JourneyStep(
            key="operation",
            label="Betrieb",
            state="current",
            url=url,
            action_label="Betriebskontext öffnen",
            reason="Das Vorhaben befindet sich im produktiven Betrieb.",
        )
    return JourneyStep(
        key="operation",
        label="Betrieb",
        state="upcoming",
        reason=(
            "Betriebsverantwortung wird erst nach einer positiven Ergebnisentscheidung relevant."
        ),
    )


def _closure_step(use_case: UseCase) -> JourneyStep:
    if use_case.status == UseCase.Status.ENDED:
        return JourneyStep(
            key="closure",
            label="Abschluss",
            state="complete",
            url=outcome_workspace_url("closure", use_case=use_case),
            action_label="Abschluss öffnen",
            reason="Das Vorhaben ist beendet; Abschlussinformationen liegen am Use Case.",
        )
    return JourneyStep(
        key="closure",
        label="Abschluss",
        state="upcoming",
        reason="Abschluss oder Stilllegung ist kein aktueller Schritt.",
    )


def build_outcome_workspace_journey(
    use_case: UseCase,
    user,
) -> JourneyState:
    """Extend the existing journey; do not create a second status engine."""

    selection_journey = build_use_case_journey(use_case, user)
    package = current_delivery_package(use_case)
    handed_over = current_handed_over_package(use_case) is not None
    measurement_complete = bool(use_case.metric_actual is not None and use_case.metric_evidence_url)

    outcome_steps = [
        _handover_step(package),
        _pilot_step(use_case, handed_over=handed_over, user=user),
        _measurement_step(use_case, handed_over=handed_over),
        _outcome_decision_step(
            use_case,
            measurement_complete=measurement_complete,
        ),
        _operation_step(use_case),
        _closure_step(use_case),
    ]
    completion_message = (
        "Lebenszyklus abgeschlossen: Das Vorhaben ist beendet."
        if use_case.status == UseCase.Status.ENDED
        else ""
    )
    return _state(
        path_label=f"{use_case.short_id} · Wirkung & Betrieb",
        steps=[*selection_journey.steps, *outcome_steps],
        completion_message=completion_message,
    )
