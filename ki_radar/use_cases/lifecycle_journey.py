from __future__ import annotations

from ki_radar.delivery.models import DeliveryPackage

from . import journey as legacy
from . import workflow
from .models import UseCase

JourneyState = workflow.JourneyState

_original_build_use_case = None


def _normalize_lifecycle_completion(
    use_case: UseCase,
    journey: JourneyState,
) -> JourneyState:
    package = use_case.delivery_packages.first()
    if package is None or package.status != DeliveryPackage.Status.HANDED_OVER:
        return journey

    completion_message = (
        "Journey abgeschlossen: Das Vorhaben wurde fachlich beendet."
        if use_case.status == UseCase.Status.ENDED
        else ""
    )
    if completion_message == journey.completion_message:
        return journey

    return JourneyState(
        path_label=journey.path_label,
        steps=journey.steps,
        next_action=journey.next_action,
        completion_message=completion_message,
    )


def build_use_case_journey(use_case: UseCase, user) -> JourneyState:
    if _original_build_use_case is None:
        raise RuntimeError("Lifecycle journey is not installed.")
    journey = _original_build_use_case(use_case, user)
    return _normalize_lifecycle_completion(use_case, journey)


def install() -> None:
    global _original_build_use_case
    if workflow.build_use_case_journey is build_use_case_journey:
        return
    _original_build_use_case = workflow.build_use_case_journey
    workflow.build_use_case_journey = build_use_case_journey
    legacy.build_use_case_journey = build_use_case_journey
