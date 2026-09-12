from pathlib import Path

from django.template.loader import get_template

ROOT = Path(__file__).resolve().parents[1]
LOCAL_STATUS = ROOT.joinpath("templates", "includes", "local_work_status.html").read_text(
    encoding="utf-8"
)
NEXT_ACTION = ROOT.joinpath("templates", "includes", "next_action.html").read_text(
    encoding="utf-8"
)
OUTCOME = ROOT.joinpath("templates", "reporting", "outcome_workspace.html").read_text(
    encoding="utf-8"
)
DISCLOSURE_JS = ROOT.joinpath("static", "js", "disclosure-navigation.js").read_text(
    encoding="utf-8"
)


def test_local_work_status_templates_compile():
    for template_name in (
        "includes/local_work_status.html",
        "includes/next_action.html",
        "reporting/outcome_workspace.html",
    ):
        get_template(template_name)


def test_status_strip_is_secondary_to_primary_action_and_scoped_to_needed_pages():
    primary = NEXT_ACTION.index('data-testid="primary-next-action"')
    local_status = NEXT_ACTION.index('includes/local_work_status.html')
    assert primary < local_status
    assert "process_analysis_detail" in NEXT_ACTION
    assert "package_detail" in NEXT_ACTION
    assert "value_stream_detail" not in LOCAL_STATUS
    assert OUTCOME.index('data-testid="outcome-primary-action"') < OUTCOME.index(
        'includes/local_work_status.html'
    )


def test_status_strip_projects_existing_domain_states_without_new_progress_engine():
    assert 'data-testid="local-work-status"' in LOCAL_STATUS
    assert "data-work-state" in LOCAL_STATUS
    assert "step.state == 'complete'" in LOCAL_STATUS
    assert "row.state == 'confirmed'" in LOCAL_STATUS
    assert "latest_validation.process_version == process_analysis.version" in LOCAL_STATUS
    assert "selected_use_case.metric_actual is not None" in LOCAL_STATUS
    assert "selected_use_case.latest_delivery.status == 'handed_over'" in LOCAL_STATUS
    assert "Erledigt" in LOCAL_STATUS
    assert "Offen" in LOCAL_STATUS
    assert "Blockiert" in LOCAL_STATUS
    assert "Optional" in LOCAL_STATUS
    assert "3 von" not in LOCAL_STATUS
    assert "Fortschritt" not in LOCAL_STATUS


def test_local_status_entries_link_to_real_work_areas_and_are_not_color_only():
    for target in (
        "assessment",
        "governance-evidence",
        "decision-history",
        "metric-title",
        "process-validation",
        "prozessanalyse",
        "loesungsoptionen",
        "outcome-measurement",
        "outcome-delivery-context",
    ):
        assert target in LOCAL_STATUS
    for marker in ("✓", "○", "!", "\u2013", "·"):
        assert marker in LOCAL_STATUS
    assert 'aria-label="Arbeitsbereiche' in LOCAL_STATUS


def test_visible_section_updates_aria_current_without_changing_domain_state():
    assert "setActiveLocalWorkTarget" in DISCLOSURE_JS
    assert 'setAttribute("aria-current", "location")' in DISCLOSURE_JS
    assert 'addEventListener("scroll"' in DISCLOSURE_JS
    assert "data-work-state" not in DISCLOSURE_JS


def test_outcome_exposes_local_anchor_targets_for_status_navigation():
    assert 'id="outcome-measurement"' in OUTCOME
    assert 'id="outcome-delivery-context"' in OUTCOME
    assert 'id="outcome-scale-review"' in OUTCOME
