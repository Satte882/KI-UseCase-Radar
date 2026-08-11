from pathlib import Path
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

from ki_radar.use_cases.journey import JourneyState, JourneyStep

ROOT = Path(__file__).resolve().parents[1]


def read_repo_text(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


DESIGN = read_repo_text("DESIGN.md")
AUDIT = read_repo_text("docs", "UI_LIFECYCLE_OWNERSHIP_AUDIT.md")
VALUE_STREAM = read_repo_text("templates", "architecture", "value_stream_detail.html")
TOPBAR = read_repo_text("templates", "includes", "context_topbar.html")
NEXT_ACTION = read_repo_text("templates", "includes", "next_action.html")
LIFECYCLE = read_repo_text("templates", "includes", "lifecycle_rail.html")
PRIMITIVES = read_repo_text("static", "css", "ui-control-room-primitives.css")


def test_design_contract_owns_each_journey_once():
    assert (
        "Eine Journey/Datenquelle darf pro Arbeitsobjekt nur eine primäre "
        "Lifecycle-Darstellung besitzen."
    ) in DESIGN
    assert "Ein echter Subworkflow ist nur zulässig" in DESIGN
    assert "Next Action erscheint pro Arbeitsobjekt genau einmal dominant" in DESIGN
    assert "keine horizontale Scrollfläche" in DESIGN


def test_audit_distinguishes_duplicates_from_real_subworkflows():
    for classification in (
        "global-only",
        "local-only",
        "duplicate-same-source",
        "semantic-subworkflow",
    ):
        assert classification in AUDIT

    for duplicate in (
        "architecture/value_stream_detail.html",
        "architecture/process_analysis_detail.html",
        "delivery/package_detail.html",
        "governance/form.html",
        "governance/review_form.html",
        "use_cases/assessment_form.html",
        "use_cases/decision_form.html",
    ):
        assert duplicate in AUDIT

    assert "use_cases/intake_wizard.html" in AUDIT
    assert "accelerator/capture_wizard.html" in AUDIT
    assert "delivery/package_form.html" in AUDIT


def test_value_stream_reference_owns_next_action_and_lifecycle_locally():
    assert "ui-control-room page-value-stream" in VALUE_STREAM
    assert "css/ui-control-room-primitives.css" in VALUE_STREAM
    assert VALUE_STREAM.count('includes/next_action.html') == 1
    assert VALUE_STREAM.count('includes/lifecycle_rail.html') == 1
    assert "includes/journey_stepper.html" not in VALUE_STREAM
    assert 'class="cr-next-action"' in VALUE_STREAM
    assert 'data-testid="primary-next-action-control"' not in VALUE_STREAM
    assert "journey.next_action.action_label" not in VALUE_STREAM


def test_value_stream_does_not_repeat_phase_add_as_primary_action():
    assert "can_edit and journey.next_action.key != 'value_stream'" in VALUE_STREAM
    assert "Weitere Phase ergänzen" in VALUE_STREAM
    assert NEXT_ACTION.count('data-testid="primary-next-action-control"') == 2
    assert "architecture" in NEXT_ACTION
    assert "value_stream_detail" in NEXT_ACTION


def test_context_topbar_explicitly_yields_value_stream_ownership():
    assert "request.resolver_match.namespace == 'architecture'" in TOPBAR
    assert "request.resolver_match.url_name == 'value_stream_detail'" in TOPBAR
    assert "owns Next Action and LifecycleRail locally" in TOPBAR

    request = RequestFactory().get("/architecture/value-streams/example/")
    request.user = AnonymousUser()
    request.resolver_match = SimpleNamespace(
        namespace="architecture",
        url_name="value_stream_detail",
    )
    step = JourneyStep(
        key="value_stream",
        label="Value Stream",
        state="current",
        url="/architecture/value-streams/example/",
        action_label="Phase ergänzen",
        reason="Die Phasenstruktur ist noch offen.",
    )
    journey = JourneyState(
        path_label="Value Stream Test",
        steps=(step,),
        next_action=step,
    )

    rendered = render_to_string(
        "includes/context_topbar.html",
        {"journey": journey, "request": request},
        request=request,
    )

    assert "Arbeitsfortschritt" not in rendered
    assert "journey-progress" not in rendered
    assert "journey-next-action-context" not in rendered


def test_canonical_lifecycle_keeps_true_links_focus_and_responsive_layout():
    assert "workflow_steps journey request as workflow" in LIFECYCLE
    assert 'href="{{ step.url }}"' in LIFECYCLE
    assert "aria-current=\"page\"" in LIFECYCLE
    assert "aria-current=\"step\"" in LIFECYCLE
    assert ".cr-lifecycle-step:focus-visible" in PRIMITIVES
    assert "@media (max-width: 760px)" in PRIMITIVES
    assert "@media (max-width: 520px)" in PRIMITIVES
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in PRIMITIVES
    assert "grid-template-columns: 1fr" in PRIMITIVES
    assert "overflow-x" not in PRIMITIVES
    for token in ("var(--success)", "var(--warning)", "var(--danger)", "var(--ice)"):
        assert token in PRIMITIVES
