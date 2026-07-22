from pathlib import Path


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def update_outcome_workspace() -> None:
    path = Path("ki_radar/use_cases/outcome_workspace.py")
    text = path.read_text(encoding="utf-8")

    helper = """def _measurement_fields_complete(use_case: UseCase) -> bool:
    return not _measurement_missing(use_case)


def _measurement_complete(use_case: UseCase) -> bool:
    if not _measurement_fields_complete(use_case) or use_case.pilot_start is None:
        return False
    return use_case.metric_measured_at >= use_case.pilot_start


def _measurement_predates_pilot(use_case: UseCase) -> bool:
    return bool(
        _measurement_fields_complete(use_case)
        and use_case.pilot_start is not None
        and use_case.metric_measured_at < use_case.pilot_start
    )


"""
    text = replace_between(
        text,
        "def _measurement_complete(use_case: UseCase) -> bool:",
        "def _has_measurement_data",
        helper,
    )

    measurement_function = text.index("def _measurement_step")
    block_start = text.index(
        "    if not handed_over or not pilot_started:", measurement_function
    )
    block_end = text.index("    if measurement_complete:", block_start)
    block = """    if not handed_over or not pilot_started:
        lifecycle_requires_pilot = use_case.status in {
            UseCase.Status.PILOT,
            UseCase.Status.OPERATION,
            UseCase.Status.ENDED,
        } or end_recorded
        return JourneyStep(
            key="measurement",
            label="Wirkungsmessung",
            state="blocked" if lifecycle_requires_pilot else "upcoming",
            reason=(
                "Dateninkonsistenz: Der Lifecycle ist bereits fortgeschritten, obwohl "
                "Übergabe oder Pilotbeginn fehlen."
                if lifecycle_requires_pilot
                else (
                    "Vorhandene Messwerte schließen keinen Pilot ab, solange kein "
                    "verbindlicher Pilotbeginn dokumentiert ist."
                    if has_data
                    else "Die Wirkungsmessung folgt nach Übergabe und gestartetem Pilot."
                )
            ),
            details=("Übergabe", "Pilotbeginn") if lifecycle_requires_pilot else (),
        )
    if _measurement_predates_pilot(use_case):
        return JourneyStep(
            key="measurement",
            label="Wirkungsmessung",
            state="upcoming",
            url=f"{edit_url}?highlight=metric_measured_at",
            action_label="Messung für aktuellen Pilot aktualisieren",
            reason=(
                "Die vorhandene Messung stammt aus der Zeit vor dem aktuellen "
                "Pilotbeginn und schließt diesen Pilot nicht ab."
            ),
            details=("Messdatum ab Pilotbeginn",),
        )
"""
    text = text[:block_start] + block + text[block_end:]
    text = text.replace("        or _has_measurement_data(use_case)\n", "", 1)
    path.write_text(text, encoding="utf-8")
    print("updated outcome workspace")


def update_golden_path_test() -> None:
    path = Path("tests/test_delivery_to_pilot.py")
    text = path.read_text(encoding="utf-8")
    block_start = text.index(
        "    outcome = build_outcome_workspace_journey(use_case, coordinator)"
    )
    block_end = text.index("\n\n\n@pytest.mark.django_db", block_start)
    block = """    outcome = build_outcome_workspace_journey(use_case, coordinator)
    outcome_steps = {step.key: step for step in outcome.steps}
    assert outcome_steps["pilot"].state == "current"
    assert outcome_steps["measurement"].state == "upcoming"
    assert outcome_steps["outcome_decision"].state == "upcoming"
    assert sum(step.state == "current" for step in outcome_steps.values()) == 1"""
    path.write_text(text[:block_start] + block + text[block_end:], encoding="utf-8")
    print("updated golden path test")


def update_consistency_tests() -> None:
    path = Path("tests/test_outcome_journey_consistency.py")
    text = path.read_text(encoding="utf-8")
    helper = """def _complete_measurement(use_case, *, measured_at=None):
    use_case.metric_actual = Decimal("2.8")
    use_case.metric_measurement_period = "Mai bis Juni 2026"
    use_case.metric_measured_at = measured_at or timezone.localdate()
    use_case.metric_evidence_url = "https://example.invalid/evidence/pilot"
    use_case.save(
        update_fields=[
            "metric_actual",
            "metric_measurement_period",
            "metric_measured_at",
            "metric_evidence_url",
            "updated_at",
        ]
    )


"""
    text = replace_between(text, "def _complete_measurement", "def _review", helper)

    marker = "@pytest.mark.django_db\ndef test_selected_view_is_marked_independently"
    marker_index = text.index(marker)
    addition = """@pytest.mark.django_db
def test_measurement_before_current_pilot_does_not_complete_pilot(
    coordinator,
    owner,
    business_unit,
):
    use_case = _use_case(owner, business_unit)
    _handed_over_package(use_case, coordinator)
    _start_pilot(use_case)
    _complete_measurement(
        use_case,
        measured_at=use_case.pilot_start - timedelta(days=1),
    )

    states = _outcome_states(build_outcome_workspace_journey(use_case, coordinator))

    assert states == {
        "handover": "complete",
        "pilot": "current",
        "measurement": "upcoming",
        "outcome_decision": "upcoming",
        "operation": "upcoming",
        "closure": "upcoming",
    }
    assert list(states.values()).count("current") == 1


"""
    path.write_text(text[:marker_index] + addition + text[marker_index:], encoding="utf-8")
    print("updated consistency tests")


def main() -> None:
    update_outcome_workspace()
    update_golden_path_test()
    update_consistency_tests()


if __name__ == "__main__":
    main()
