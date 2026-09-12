from __future__ import annotations

from dataclasses import replace

from ki_radar.delivery.handover import current_handed_over_package

from . import outcome_workspace
from .models import UseCase

_original_build_outcome = None


def build_outcome_workspace_journey(use_case: UseCase, user):
    if _original_build_outcome is None:
        raise RuntimeError("Lean outcome projection is not installed.")
    journey = _original_build_outcome(use_case, user)
    if use_case.status != UseCase.Status.ENDED:
        return journey

    end_recorded = use_case.reviews.filter(
        decision="end",
        previous_status__in=(UseCase.Status.PILOT, UseCase.Status.OPERATION),
        new_status=UseCase.Status.ENDED,
    ).exists()
    if not end_recorded:
        # This remains a true invariant violation. The canonical command path prevents new cases.
        return journey

    details = []
    if not str(use_case.ending_reason or "").strip():
        details.append("Readiness offen: Beendigungsgrund")
    if not str(use_case.data_and_access_handling or "").strip():
        details.append("Readiness offen: Umgang mit Daten und Zugängen")

    steps = []
    for step in journey.steps:
        if step.key == "closure":
            steps.append(
                replace(
                    step,
                    state="complete",
                    action_label="Abschluss öffnen",
                    reason=(
                        "Der Use Case ist fachlich beendet. Offene Abschlussinformationen "
                        "bleiben als Readiness sichtbar und ändern den Lifecycle nicht."
                    ),
                    details=tuple(details),
                )
            )
        else:
            steps.append(step)
    return outcome_workspace._state(
        path_label=journey.path_label,
        steps=steps,
        completion_message="Lebenszyklus abgeschlossen: Das Vorhaben ist fachlich beendet.",
    )


def install() -> None:
    global _original_build_outcome
    if outcome_workspace.build_outcome_workspace_journey is build_outcome_workspace_journey:
        return
    # Handover truth is a Delivery-owned persisted milestone. Readiness findings remain visible
    # but must not retroactively invalidate a completed handover.
    outcome_workspace.current_handed_over_package = current_handed_over_package
    _original_build_outcome = outcome_workspace.build_outcome_workspace_journey
    outcome_workspace.build_outcome_workspace_journey = build_outcome_workspace_journey
