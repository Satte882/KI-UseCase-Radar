from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.delivery.models import DeliveryPackage
from ki_radar.reviews.forms import ReviewForm
from ki_radar.reviews.models import Review
from ki_radar.use_cases.models import UseCase


def _use_case(owner, business_unit, *, status=UseCase.Status.PILOT):
    return UseCase.objects.create(
        title="Pilot für Lieferantenauswahl",
        problem_statement="Angebote werden manuell verglichen.",
        business_unit=business_unit,
        affected_process="Lieferantenauswahl",
        business_owner=owner,
        expected_benefit="Durchlaufzeit senken.",
        status=status,
        metric_name="Durchlaufzeit",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Tage",
        metric_baseline=Decimal("5"),
        metric_target=Decimal("3"),
    )


def _package(use_case, coordinator, *, external_url="", status=DeliveryPackage.Status.HANDED_OVER):
    return DeliveryPackage.objects.create(
        use_case=use_case,
        version=1,
        status=status,
        created_by=coordinator,
        external_delivery_url=external_url,
        handed_over_by=coordinator if status == DeliveryPackage.Status.HANDED_OVER else None,
        handed_over_at=timezone.now() if status == DeliveryPackage.Status.HANDED_OVER else None,
    )


@pytest.mark.django_db
def test_handover_has_its_own_workspace_context(client, coordinator, owner, business_unit):
    use_case = _use_case(owner, business_unit, status=UseCase.Status.REVIEW)
    package = _package(use_case, coordinator, status=DeliveryPackage.Status.READY)
    client.force_login(coordinator)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "handover", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    content = response.content.decode()
    assert response.context["active_stage"] == "handover"
    assert action["action_label"] == "Übergabe durchführen"
    assert action["url"] == package.get_absolute_url()
    assert "Aktiver Bereich" in content
    assert "Übergabe" in content


@pytest.mark.django_db
def test_running_pilot_opens_real_external_delivery_link(
    client,
    coordinator,
    owner,
    business_unit,
):
    use_case = _use_case(owner, business_unit)
    external_url = "https://example.invalid/delivery/pilot-42"
    _package(use_case, coordinator, external_url=external_url)
    client.force_login(owner)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "pilot", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    content = response.content.decode()
    assert action["action_label"] == "Externen Pilot öffnen"
    assert action["url"] == external_url
    assert action["external"] is True
    assert "Pilotübersicht öffnen" not in content
    assert 'target="_blank"' in content


@pytest.mark.django_db
def test_handed_over_pilot_without_external_link_has_intentional_empty_state(
    client,
    coordinator,
    owner,
    business_unit,
):
    use_case = _use_case(owner, business_unit)
    _package(use_case, coordinator)
    client.force_login(coordinator)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "pilot", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    content = response.content.decode()
    assert action["url"] == ""
    assert "übergebene Package ist unveränderlich" in action["reason"]
    assert "Keine Aktion erforderlich" in content
    assert "Delivery-Link ergänzen" not in content


@pytest.mark.django_db
def test_effect_deep_link_targets_existing_metric_fields(client, owner, business_unit):
    use_case = _use_case(owner, business_unit)
    client.force_login(owner)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "effect", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    expected_url = (
        f"{reverse('use_cases:edit', kwargs={'pk': use_case.pk})}?highlight=metric_actual"
    )
    assert action["action_label"] == "Ist-Wert erfassen"
    assert action["url"].endswith(expected_url)


@pytest.mark.django_db
def test_go_live_action_uses_existing_review_form(client, coordinator, owner, business_unit):
    use_case = _use_case(owner, business_unit)
    use_case.metric_actual = Decimal("2.8")
    use_case.metric_measurement_period = "Mai bis Juni 2026"
    use_case.metric_measured_at = timezone.localdate()
    use_case.metric_evidence_url = "https://example.invalid/evidence/pilot"
    use_case.save()
    client.force_login(coordinator)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "decision", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    assert action["action_label"] == "Go-live entscheiden"
    assert action["url"] == (
        f"{reverse('reviews:create', kwargs={'use_case_id': use_case.pk})}?action=go_live"
    )

    form = ReviewForm(
        use_case=use_case,
        actor=coordinator,
        requested_action="go_live",
    )
    assert form.fields["decision"].initial == Review.Decision.GO_LIVE
    assert form.fields["new_status"].initial == UseCase.Status.OPERATION


@pytest.mark.django_db
def test_operation_without_due_review_renders_neutral_status(
    client,
    coordinator,
    owner,
    business_unit,
):
    use_case = _use_case(owner, business_unit, status=UseCase.Status.OPERATION)
    use_case.next_review_date = timezone.localdate() + timedelta(days=30)
    use_case.save(update_fields=["next_review_date", "updated_at"])
    client.force_login(coordinator)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "operation", "use_case": use_case.pk},
    )

    action = response.context["active_stage_action"]
    content = response.content.decode()
    assert action["url"] == ""
    assert "Aktuell keine Aktion erforderlich" in action["reason"]
    assert "Keine Aktion erforderlich" in content


@pytest.mark.django_db
def test_due_operation_review_and_closure_use_existing_review_form(
    client,
    coordinator,
    owner,
    business_unit,
):
    use_case = _use_case(owner, business_unit, status=UseCase.Status.OPERATION)
    use_case.next_review_date = timezone.localdate()
    use_case.save(update_fields=["next_review_date", "updated_at"])
    client.force_login(coordinator)

    operation_response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "operation", "use_case": use_case.pk},
    )
    closure_response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "closure", "use_case": use_case.pk},
    )

    assert operation_response.context["active_stage_action"]["action_label"] == (
        "Review dokumentieren"
    )
    assert closure_response.context["active_stage_action"]["action_label"] == (
        "Abschluss dokumentieren"
    )

    form = ReviewForm(
        use_case=use_case,
        actor=coordinator,
        requested_action="closure",
    )
    assert form.fields["decision"].initial == Review.Decision.END
    assert form.fields["new_status"].initial == UseCase.Status.ENDED


@pytest.mark.django_db
def test_sidebar_uses_compact_account_menu(client, technical_admin, owner, business_unit):
    use_case = _use_case(owner, business_unit)
    client.force_login(technical_admin)

    response = client.get(
        reverse("reporting:outcome_workspace"),
        {"stage": "pilot", "use_case": use_case.pk},
    )

    content = response.content.decode()
    assert "sidebar-account-trigger" in content
    assert "Administration" in content
    assert "Angemeldet" not in content
    assert "btn-ghost w-100" not in content
