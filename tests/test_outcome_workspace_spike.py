from pathlib import Path

import pytest
from django.urls import reverse

from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.outcome_workspace import build_outcome_workspace_journey
from ki_radar.use_cases.workflow import JourneyState

ROOT = Path(__file__).resolve().parents[1]


def _use_case(owner, business_unit):
    return UseCase.objects.create(
        title="Pilot für Rechnungsprüfung",
        problem_statement="Die Prüfung ist langsam und erzeugt Rückfragen.",
        business_unit=business_unit,
        affected_process="Eingangsrechnung prüfen",
        business_owner=owner,
        expected_benefit="Prüfzeit messbar senken.",
        status=UseCase.Status.PILOT,
        metric_name="Prüfzeit je Rechnung",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Minuten",
        metric_baseline=11,
        metric_target=5,
    )


def test_outcome_workspace_assets_document_scope_and_variants():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "reporting" / "outcome_workspace.html").read_text(
        encoding="utf-8"
    )
    documentation = (ROOT / "docs" / "OUTCOME_WORKSPACE.md").read_text(encoding="utf-8")

    assert "sidebar-workspace-separator" in base
    assert "Wirkung &amp; Betrieb" in base
    assert "css/outcome-workspace.css" in base
    assert "A · Arbeitsraum wechselt" in template
    assert "B · Gesamtleiste" in template
    assert "manueller Review-Snapshot" in template
    assert "keine Live-Synchronisation" in documentation
    assert "keine zweite Journey-Engine" in documentation


@pytest.mark.django_db
def test_outcome_journey_extends_existing_journey_state(owner, business_unit):
    use_case = _use_case(owner, business_unit)

    journey = build_outcome_workspace_journey(use_case, owner, layout="split")
    keys = [step.key for step in journey.steps]

    assert isinstance(journey, JourneyState)
    assert keys[:2] == ["value_stream", "focus"]
    assert "delivery" in keys
    assert keys[-6:] == [
        "handover",
        "pilot",
        "measurement",
        "outcome_decision",
        "operation",
        "closure",
    ]
    assert journey.next_action is not None
    assert journey.next_action.key in {"use_case", "delivery", "handover", "pilot", "measurement"}


@pytest.mark.django_db
def test_outcome_workspace_renders_both_lifecycle_segments(client, owner, business_unit):
    use_case = _use_case(owner, business_unit)
    client.force_login(owner)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {
            "stage": "effect",
            "layout": "continuous",
            "use_case": use_case.pk,
        },
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["active_stage"] == "effect"
    assert response.context["layout"] == "continuous"
    assert response.context["journey"].path_label.endswith("Wirkung & Betrieb")
    assert "Arbeitsraum 2 · Wirkung &amp; Betrieb" in content
    assert "Discovery" in content
    assert "Fokus &amp; Priorisierung" in content
    assert "Ergebnisentscheidung" in content
    assert "Review-Snapshot statt Projektmanagement" in content
    assert "Externes Delivery-System" in content


@pytest.mark.django_db
def test_outcome_workspace_defaults_invalid_parameters(client, owner, business_unit):
    _use_case(owner, business_unit)
    client.force_login(owner)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "unknown", "layout": "unknown", "use_case": "invalid"},
    )

    assert response.status_code == 200
    assert response.context["active_stage"] == "pilot"
    assert response.context["layout"] == "split"
    assert response.context["selected_use_case"] is not None
