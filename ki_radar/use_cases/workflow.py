from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from ki_radar.architecture.focus import ValueStreamFocus, get_value_stream_focus
from ki_radar.architecture.models import ProcessAnalysis, ValueStream
from ki_radar.delivery.models import DeliveryPackage

from . import journey as legacy

JourneyState = legacy.JourneyState
JourneyStep = legacy.JourneyStep
LEGACY_BUILD_USE_CASE = legacy.build_use_case_journey
LEGACY_BUILD_PROCESS = legacy.build_process_analysis_journey
LEGACY_BUILD_VALUE_STREAM = legacy.build_value_stream_journey


def _state(
    *,
    path_label: str,
    steps: list[JourneyStep],
    completion_message: str = "",
) -> JourneyState:
    return JourneyState(
        path_label=path_label,
        steps=tuple(steps),
        next_action=next(
            (step for step in steps if step.state in {"current", "blocked"}),
            None,
        ),
        completion_message=completion_message,
    )


def _focus_step(value_stream: ValueStream, *, terminal_as_complete: bool = False) -> JourneyStep:
    focus = get_value_stream_focus(value_stream)
    edit_url = reverse("architecture:value_stream_update", kwargs={"pk": value_stream.pk})
    if focus is None:
        return JourneyStep(
            key="focus",
            label="Fokus & Priorisierung",
            state="blocked",
            url=edit_url,
            action_label="Screening ergänzen",
            reason="Der Value Stream wurde noch nicht anhand einheitlicher Fokus-Kriterien bewertet.",
            details=("Fachdomäne", "Business Capability", "Impact, Potenzial, Daten und Aufwand"),
        )
    if focus.missing_screening_fields:
        return JourneyStep(
            key="focus",
            label="Fokus & Priorisierung",
            state="blocked",
            url=edit_url,
            action_label="Screening vervollständigen",
            reason="Die Fokusentscheidung ist noch nicht belastbar dokumentiert.",
            details=focus.missing_screening_fields,
        )
    if focus.status == ValueStreamFocus.Status.SELECTED:
        return JourneyStep(
            key="focus",
            label="Fokus & Priorisierung",
            state="complete",
            url=value_stream.get_absolute_url(),
            action_label="Fokusentscheidung öffnen",
            reason="Der Value Stream wurde für einen Deep Dive ausgewählt.",
        )
    if focus.status == ValueStreamFocus.Status.CANDIDATE:
        return JourneyStep(
            key="focus",
            label="Fokus & Priorisierung",
            state="current",
            url=edit_url,
            action_label="Fokusentscheidung treffen",
            reason="Das Screening ist vollständig; die Auswahlentscheidung steht noch aus.",
        )
    if focus.is_terminal:
        return JourneyStep(
            key="focus",
            label="Fokus & Priorisierung",
            state="complete" if terminal_as_complete else "optional",
            url=value_stream.get_absolute_url(),
            action_label="Fokusentscheidung öffnen",
            reason=f"Fokusentscheidung: {focus.get_status_display()}.",
        )
    return JourneyStep(
        key="focus",
        label="Fokus & Priorisierung",
        state="current",
        url=edit_url,
        action_label="Value Stream bewerten",
        reason="Impact, Potenzial, Datenzugänglichkeit und Veränderungsaufwand bewerten.",
    )


def _insert_focus(journey: JourneyState, focus_step: JourneyStep) -> JourneyState:
    steps = [step for step in journey.steps if step.key != "focus"]
    insert_at = next(
        (index + 1 for index, step in enumerate(steps) if step.key == "value_stream"),
        0,
    )
    steps.insert(insert_at, focus_step)
    return _state(
        path_label=journey.path_label,
        steps=steps,
        completion_message=journey.completion_message,
    )


def _focus_terminal_journey(value_stream: ValueStream, focus: ValueStreamFocus) -> JourneyState:
    stages = list(value_stream.stages.all())
    steps = [
        JourneyStep(
            key="value_stream",
            label="Value Stream",
            state="complete" if stages else "current",
            url=value_stream.get_absolute_url(),
            reason=(
                f"{len(stages)} End-to-End-Phasen sind erfasst."
                if stages
                else "Die End-to-End-Phasen sind noch nicht erfasst."
            ),
        ),
        _focus_step(value_stream, terminal_as_complete=True),
        JourneyStep(
            key="process",
            label="Prozessanalyse",
            state="optional",
            reason="Für einen nicht ausgewählten Value Stream ist kein Deep Dive erforderlich.",
        ),
        JourneyStep(key="solution", label="Lösungsoption", state="optional"),
        JourneyStep(key="use_case", label="Use Case", state="optional"),
        JourneyStep(key="assessment", label="Bewertung", state="optional"),
        JourneyStep(key="approval", label="Freigabe", state="optional"),
        JourneyStep(key="delivery", label="Delivery", state="optional"),
    ]
    return _state(
        path_label="Systematische Discovery",
        steps=steps,
        completion_message=f"Discovery beendet: {focus.get_status_display()}.",
    )


def build_value_stream_journey(value_stream: ValueStream, user) -> JourneyState:
    focus = get_value_stream_focus(value_stream)
    if focus is not None and focus.is_terminal:
        return _focus_terminal_journey(value_stream, focus)

    legacy_journey = LEGACY_BUILD_VALUE_STREAM(value_stream, user)
    focus_step = _focus_step(value_stream)
    if focus is None or not focus.is_selected:
        steps = []
        for step in legacy_journey.steps:
            if step.key == "value_stream":
                steps.append(step)
                steps.append(focus_step)
                continue
            steps.append(
                JourneyStep(
                    key=step.key,
                    label=step.label,
                    state="upcoming",
                    reason="Der Deep Dive beginnt erst nach der Auswahl des Value Streams.",
                )
            )
        if not any(step.key == "focus" for step in steps):
            steps.insert(1 if steps else 0, focus_step)
        return _state(path_label="Systematische Discovery", steps=steps)
    return _insert_focus(legacy_journey, focus_step)


def build_process_analysis_journey(process_analysis: ProcessAnalysis, user) -> JourneyState:
    value_stream = process_analysis.stage.value_stream
    focus = get_value_stream_focus(value_stream)
    if focus is not None and focus.is_terminal:
        return _focus_terminal_journey(value_stream, focus)
    legacy_journey = LEGACY_BUILD_PROCESS(process_analysis, user)
    focus_step = _focus_step(value_stream)
    if focus is None or not focus.is_selected:
        steps = []
        for step in legacy_journey.steps:
            if step.key == "value_stream":
                steps.append(step)
                steps.append(focus_step)
            else:
                steps.append(
                    JourneyStep(
                        key=step.key,
                        label=step.label,
                        state="upcoming",
                        reason="Der Deep Dive ist bis zur Fokusentscheidung zurückgestellt.",
                    )
                )
        return _state(path_label="Systematische Discovery", steps=steps)
    return _insert_focus(legacy_journey, focus_step)


def build_use_case_journey(use_case, user) -> JourneyState:
    legacy_journey = LEGACY_BUILD_USE_CASE(use_case, user)
    try:
        origin = use_case.architecture_origin
    except ObjectDoesNotExist:
        origin = None
    if origin is None:
        steps = [
            JourneyStep(
                key="value_stream",
                label="Discovery",
                state="optional",
                reason="Der Use Case wurde direkt erfasst.",
            ),
            JourneyStep(
                key="focus",
                label="Fokus & Priorisierung",
                state="optional",
                reason="Direkter Intake ohne vorgelagertes Value-Stream-Screening.",
            ),
            *legacy_journey.steps,
        ]
        return _state(
            path_label=legacy_journey.path_label,
            steps=steps,
            completion_message=legacy_journey.completion_message,
        )
    return _insert_focus(
        legacy_journey,
        _focus_step(origin.stage.value_stream),
    )


def build_delivery_package_journey(package: DeliveryPackage, user) -> JourneyState:
    return build_use_case_journey(package.use_case, user)


def install() -> None:
    legacy.build_value_stream_journey = build_value_stream_journey
    legacy.build_process_analysis_journey = build_process_analysis_journey
    legacy.build_use_case_journey = build_use_case_journey
    legacy.build_delivery_package_journey = build_delivery_package_journey
