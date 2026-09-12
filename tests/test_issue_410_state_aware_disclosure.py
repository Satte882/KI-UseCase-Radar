from pathlib import Path

import pytest

from ki_radar.use_cases.models import UseCase

ROOT = Path(__file__).resolve().parents[1]


def read_repo_text(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


USE_CASE_DETAIL = read_repo_text("templates", "use_cases", "detail.html")
DECISION_STATE = read_repo_text("templates", "includes", "decision_state.html")
DELIVERY_DETAIL = read_repo_text("templates", "delivery", "package_detail.html")
PROCESS_DETAIL = read_repo_text("templates", "architecture", "process_analysis_detail.html")
VALUE_STREAM_DETAIL = read_repo_text("templates", "architecture", "value_stream_detail.html")
OUTCOME_WORKSPACE = read_repo_text("templates", "reporting", "outcome_workspace.html")
BASE = read_repo_text("templates", "base.html")
DISCLOSURE_NAVIGATION = read_repo_text("static", "js", "disclosure-navigation.js")


def test_active_gate_readiness_is_not_hidden_behind_disclosure():
    assert 'id="upcoming-gate-readiness"' in DECISION_STATE
    assert 'data-testid="upcoming-gate-readiness"' in DECISION_STATE
    assert "Nächstes Gate vorbereiten" in DECISION_STATE

    readiness_start = DECISION_STATE.index('id="upcoming-gate-readiness"')
    readiness_end = DECISION_STATE.index("{% endif %}", readiness_start)
    readiness = DECISION_STATE[readiness_start:readiness_end]
    assert "<details" not in readiness
    assert "blocker-actions" in readiness


def test_use_case_governance_keeps_status_and_open_paths_visible():
    governance_start = USE_CASE_DETAIL.index('id="governance-evidence"')
    disclosure_start = USE_CASE_DETAIL.index('id="governance-evidence-details"')
    governance_summary = USE_CASE_DETAIL[governance_start:disclosure_start]
    active_states = "status.state == 'open' or status.state == 'not_assessed'"
    old_always_open_panel = '<details class="uc-side-panel" id="governance-evidence" open>'
    governance_details = (
        '<details class="architecture-disclosure mt-3" '
        'id="governance-evidence-details">'
    )

    assert 'data-testid="governance-status-summary"' in governance_summary
    assert active_states in governance_summary
    assert "Prüfartefakt öffnen" in governance_summary
    assert "governance:create" in governance_summary
    assert "notifications:evidence_create" in governance_summary
    assert old_always_open_panel not in USE_CASE_DETAIL
    assert governance_details in USE_CASE_DETAIL


def test_secondary_information_stays_collapsible_after_state_aware_hardening():
    for marker in (
        'id="assessment-evidence"',
        'id="metric-evidence"',
        'id="origin-context"',
        'id="review-copilot"',
        'id="decision-history"',
    ):
        marker_pos = USE_CASE_DETAIL.index(marker)
        details_pos = USE_CASE_DETAIL.rfind("<details", 0, marker_pos)
        assert details_pos >= 0

    assert '{% if row.is_primary %} open{% endif %}' in DELIVERY_DETAIL
    assert 'data-testid="process-validation-evidence"' in PROCESS_DETAIL
    assert "Validierungsnachweis und Historie" in PROCESS_DETAIL
    assert 'data-testid="value-stream-screening-details"' in VALUE_STREAM_DETAIL
    assert "Screening- und Einordnungsdetails" in VALUE_STREAM_DETAIL
    assert '<details class="outcome-use-case-context">' in OUTCOME_WORKSPACE
    assert '<details class="outcome-boundary-details">' in OUTCOME_WORKSPACE


def test_hash_navigation_reveals_native_disclosure_targets_globally():
    hash_listener = 'window.addEventListener("hashchange", revealHashTarget)'

    assert "js/disclosure-navigation.js" in BASE
    assert hash_listener in DISCLOSURE_NAVIGATION
    assert 'target.matches("details")' in DISCLOSURE_NAVIGATION
    assert 'target.closest("details")' in DISCLOSURE_NAVIGATION
    assert "disclosure.open = true" in DISCLOSURE_NAVIGATION
    assert "focus({ preventScroll: true })" in DISCLOSURE_NAVIGATION


@pytest.mark.django_db
def test_unassessed_governance_work_is_visible_on_use_case_detail(
    client,
    owner,
    coordinator,
    business_unit,
):
    use_case = UseCase.objects.create(
        title="Governance-Arbeit sichtbar halten",
        problem_statement="Offene Governance-Arbeit darf nicht hinter Disclosure verschwinden.",
        business_unit=business_unit,
        affected_process="Kernprozess",
        submitter=owner,
        business_owner=owner,
        coordinator=coordinator,
        expected_benefit="Offene Arbeit ist ohne Suchaufwand erkennbar.",
        status=UseCase.Status.REVIEW,
    )
    client.force_login(coordinator)

    response = client.get(use_case.get_absolute_url())

    assert response.status_code == 200
    html = response.content.decode()
    summary_start = html.index('data-testid="governance-status-summary"')
    disclosure_start = html.index('id="governance-evidence-details"')
    visible_summary = html[summary_start:disclosure_start]
    assert "Noch nicht bewertet" in visible_summary
    assert "Prüfartefakt öffnen" in visible_summary
    assert "Governance-Screening" in visible_summary
