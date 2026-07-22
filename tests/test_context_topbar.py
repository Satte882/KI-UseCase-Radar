from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_base_uses_contextual_topbar_instead_of_static_status():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")

    assert "includes/context_topbar.html" in base
    assert "css/context-topbar.css" in base
    assert "Discovery · Portfolio · Governance · Delivery" not in base
    assert "System bereit" not in base


def test_context_topbar_contains_progress_and_next_action():
    topbar = (ROOT / "templates" / "includes" / "context_topbar.html").read_text(
        encoding="utf-8"
    )
    stylesheet = (ROOT / "static" / "css" / "context-topbar.css").read_text(
        encoding="utf-8"
    )

    assert 'aria-label="Arbeitsfortschritt"' in topbar
    assert "journey.steps" in topbar
    assert "journey.next_action" in topbar
    assert "Nächster Schritt" in topbar
    assert "journey-progress-current" in stylesheet
    assert "journey-progress-blocked" in stylesheet
    assert "journey-topbar-next" in stylesheet
