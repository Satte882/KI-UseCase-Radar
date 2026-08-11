from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "use_cases" / "detail.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "css" / "ui-control-room-use-case.css").read_text(
    encoding="utf-8"
)
JOURNEY = (ROOT / "templates" / "includes" / "journey_stepper.html").read_text(
    encoding="utf-8"
)


def test_use_case_detail_opts_into_control_room_with_page_local_work_object_css():
    assert "{% block body_class %}ui-control-room page-use-case{% endblock %}" in TEMPLATE
    shared = "css/ui-control-room-primitives.css"
    page = "css/ui-control-room-use-case.css"
    assert shared in TEMPLATE
    assert page in TEMPLATE
    assert TEMPLATE.index(shared) < TEMPLATE.index(page)
    assert ".ui-control-room.page-use-case" in CSS


def test_decision_workspace_hierarchy_places_decisions_before_secondary_information():
    expected_order = (
        'id="use-case-overview"',
        'id="decision-state"',
        'id="decision-readiness"',
        'id="next-action"',
        'id="lifecycle-orientation"',
        'id="assessment"',
        'id="metric-title"',
        'id="business-context-title"',
        'id="copilot-title"',
        'id="decision-history-title"',
    )
    positions = [TEMPLATE.index(marker) for marker in expected_order]
    assert positions == sorted(positions)


def test_all_existing_use_case_actions_remain_reachable_with_existing_permissions():
    routes = (
        "use_cases:edit",
        "reviews:create",
        "use_cases:assessment_create",
        "use_cases:approval_decision_create",
        "use_cases:second_approval_review",
        "governance:create",
        "notifications:evidence_create",
        "use_cases:copilot",
    )
    for route in routes:
        assert route in TEMPLATE

    assert "{% if can_edit %}" in TEMPLATE
    assert "{% if nav_is_coordinator %}" in TEMPLATE
    assert "journey.next_action.key != 'assessment'" in TEMPLATE
    assert "journey.next_action.key != 'approval'" in TEMPLATE
    assert "journey.next_action.key != 'governance'" in TEMPLATE


def test_lifecycle_is_local_orientation_and_keeps_true_link_semantics():
    assert ".app-topbar-journey" in CSS
    assert "display: none" in CSS
    assert 'href="{{ step.url }}"' in JOURNEY
    assert "{% include \"includes/journey_stepper.html\" %}" in TEMPLATE
    assert "journey-stepper" in CSS


def test_blocker_links_and_second_approval_remain_true_links():
    assert 'href="{{ first_blocker.target_href }}"' in TEMPLATE
    assert 'href="{{ blocker.target_href }}"' in TEMPLATE
    assert "use_cases:second_approval_review" in TEMPLATE
    assert "disabled" not in TEMPLATE[TEMPLATE.index('id="decision-readiness"') : TEMPLATE.index('id="assessment"')]


def test_work_object_patterns_remain_page_local_until_gate_b():
    assert "uc-decision-state" in TEMPLATE
    assert "uc-lifecycle" in TEMPLATE
    assert ".ui-control-room.page-use-case .uc-decision-state" in CSS
    assert ".ui-control-room.page-use-case .uc-lifecycle" in CSS
    assert "@media (max-width: 1180px)" in CSS
    assert "@media (max-width: 920px)" in CSS
    assert "@media (max-width: 720px)" in CSS
    assert "@media (max-width: 480px)" in CSS


def test_page_specific_css_uses_semantic_tokens_without_new_raw_colors():
    assert "#" not in CSS
    assert "rgb(" not in CSS
    assert "hsl(" not in CSS
    assert "var(--ice)" in CSS
    assert "var(--line-soft)" in CSS
    assert "var(--muted)" in CSS
    assert "var(--warning)" in CSS
    assert "var(--danger)" in CSS
