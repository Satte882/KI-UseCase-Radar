from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from ki_radar.governance.models import GovernanceAssessment
from ki_radar.use_cases.copilot import CopilotUnavailable, analyze_use_case
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.services import (
    check_go_live,
    check_pilot_start,
    current_decision_check,
    validate_target_status,
)


@pytest.fixture
def decision_use_case(owner, coordinator, business_unit):
    return UseCase.objects.create(
        title="Rechnungsprüfung",
        problem_statement="Rechnungen werden manuell geprüft.",
        business_unit=business_unit,
        affected_process="Eingangsrechnung",
        business_owner=owner,
        coordinator=coordinator,
        expected_benefit="Prüfzeit reduzieren",
        data_sources="ERP und Dokumentenablage",
        next_review_date=timezone.localdate() + timedelta(days=14),
        planned_pilot_end=timezone.localdate() + timedelta(days=30),
    )


@pytest.mark.django_db
def test_idea_is_checked_for_review_before_pilot(decision_use_case):
    decision_use_case.status = UseCase.Status.IDEA

    check = current_decision_check(decision_use_case)

    assert check.target_status == UseCase.Status.REVIEW
    assert check.title == UseCase.Status.REVIEW.label
    assert "Primäre Erfolgsmetrik" not in check.blockers


@pytest.mark.django_db
def test_pilot_start_is_blocked_without_structured_metric(decision_use_case, coordinator):
    GovernanceAssessment.objects.create(
        use_case=decision_use_case,
        assessment_date=timezone.localdate(),
        reviewer=coordinator,
        basis_version="2026-01",
        result=GovernanceAssessment.Result.NO_FLAGS,
        rationale="Keine Hinweise",
    )

    check = check_pilot_start(decision_use_case)

    assert check.state == "blocked"
    assert "Primäre Erfolgsmetrik" in check.blockers
    with pytest.raises(ValidationError):
        validate_target_status(decision_use_case, UseCase.Status.PILOT)


@pytest.mark.django_db
def test_go_live_compares_target_and_actual(decision_use_case, coordinator):
    decision_use_case.status = UseCase.Status.PILOT
    decision_use_case.technical_owner = coordinator
    decision_use_case.one_time_cost = Decimal("5000")
    decision_use_case.recurring_cost = Decimal("300")
    decision_use_case.support_responsibility = "IT-Service"
    decision_use_case.human_oversight = "Fachliche Freigabe bleibt manuell"
    decision_use_case.metric_name = "Prüfzeit je Rechnung"
    decision_use_case.metric_type = UseCase.MetricType.DURATION
    decision_use_case.metric_direction = UseCase.MetricDirection.LOWER
    decision_use_case.metric_unit = "Minuten"
    decision_use_case.metric_baseline = Decimal("11")
    decision_use_case.metric_target = Decimal("8.25")
    decision_use_case.metric_actual = Decimal("8.9")
    decision_use_case.metric_measurement_method = "100 Rechnungen"
    decision_use_case.metric_measurement_period = "Pilotwochen 5 bis 8"
    decision_use_case.metric_measured_at = timezone.localdate()
    decision_use_case.metric_evidence_url = "https://example.invalid/evidence"
    decision_use_case.save()

    check = check_go_live(decision_use_case)

    assert check.state == "review"
    assert decision_use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED
    assert "Pilotziel wurde nicht erreicht" in check.warnings[0]


@pytest.mark.django_db
def test_go_live_rechecks_complete_target_metric(decision_use_case, coordinator):
    decision_use_case.status = UseCase.Status.PILOT
    decision_use_case.technical_owner = coordinator
    decision_use_case.one_time_cost = Decimal("5000")
    decision_use_case.recurring_cost = Decimal("300")
    decision_use_case.support_responsibility = "IT-Service"
    decision_use_case.human_oversight = "Fachliche Freigabe bleibt manuell"
    decision_use_case.metric_actual = Decimal("8.9")
    decision_use_case.metric_measurement_period = "Pilotwochen 5 bis 8"
    decision_use_case.metric_measured_at = timezone.localdate()
    decision_use_case.metric_evidence_url = "https://example.invalid/evidence"
    decision_use_case.save()

    check = check_go_live(decision_use_case)

    assert check.state == "blocked"
    assert "Primäre Erfolgsmetrik" in check.blockers
    assert "Zielwert" in check.blockers


@pytest.mark.django_db
def test_metric_result_is_achieved_for_lower_target(decision_use_case):
    decision_use_case.metric_name = "Prüfzeit"
    decision_use_case.metric_direction = UseCase.MetricDirection.LOWER
    decision_use_case.metric_target = Decimal("8.25")
    decision_use_case.metric_actual = Decimal("8.0")

    assert decision_use_case.metric_result == UseCase.MetricResult.ACHIEVED


@pytest.mark.django_db
def test_copilot_is_optional_without_openrouter_key(settings, decision_use_case):
    settings.OPENROUTER_API_KEY = ""

    with pytest.raises(CopilotUnavailable, match="Kein OpenRouter API-Key"):
        analyze_use_case(decision_use_case)


@pytest.mark.django_db
def test_copilot_endpoint_rejects_non_coordinator(client, owner, decision_use_case):
    client.force_login(owner)

    response = client.post(reverse("use_cases:copilot", args=[decision_use_case.pk]))

    assert response.status_code == 403
