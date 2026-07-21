from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.use_cases.models import (
    BenefitMeasurement,
    DecisionAssessment,
    StrategicObjective,
    UseCase,
)
from ki_radar.use_cases.services import check_pilot_start


@pytest.fixture
def strategic_objective(coordinator):
    return StrategicObjective.objects.create(
        title="Durchlaufzeit senken",
        description="Kernprozesse schneller und verlässlicher abwickeln.",
        owner=coordinator,
        target_kpi="Durchlaufzeit",
        target_value="-20 %",
    )


@pytest.fixture
def strategy_use_case(owner, coordinator, business_unit, strategic_objective):
    return UseCase.objects.create(
        title="Rechnungsprüfung",
        problem_statement="Rechnungen werden manuell geprüft.",
        business_unit=business_unit,
        affected_process="Eingangsrechnung",
        business_owner=owner,
        coordinator=coordinator,
        strategic_objective=strategic_objective,
        strategy_contribution="Automatisierte Vorprüfung reduziert manuelle Liegezeiten.",
        expected_benefit="Prüfzeit reduzieren",
        data_sources="ERP und Dokumentenablage",
        next_review_date=timezone.localdate() + timedelta(days=14),
        planned_pilot_end=timezone.localdate() + timedelta(days=30),
        metric_name="Prüfzeit je Rechnung",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Minuten",
        metric_baseline=Decimal("11"),
        metric_target=Decimal("8.25"),
        metric_measurement_method="100 repräsentative Rechnungen",
    )


def assessment_payload(*, business_value=UseCase.Level.HIGH):
    confidence = DecisionAssessment.Confidence.HIGH
    return {
        "assessment_date": timezone.localdate(),
        "business_value": business_value,
        "business_value_confidence": confidence,
        "business_value_rationale": "Zeitersparnis ist durch Prozessmessung belegt.",
        "business_value_evidence_url": "https://example.invalid/value",
        "strategic_fit": UseCase.Level.HIGH,
        "strategic_fit_confidence": confidence,
        "strategic_fit_rationale": "Der Use Case zahlt direkt auf die Durchlaufzeit ein.",
        "strategic_fit_evidence_url": "https://example.invalid/strategy",
        "technical_feasibility": UseCase.Level.MEDIUM,
        "technical_feasibility_confidence": confidence,
        "technical_feasibility_rationale": "Schnittstellen und Dokumenttypen wurden geprüft.",
        "technical_feasibility_evidence_url": "https://example.invalid/technology",
        "data_readiness": UseCase.Level.MEDIUM,
        "data_readiness_confidence": confidence,
        "data_readiness_rationale": "Repräsentative Dokumente liegen für den Pilot vor.",
        "data_readiness_evidence_url": "https://example.invalid/data",
        "risk_complexity": UseCase.Level.LOW,
        "risk_complexity_confidence": confidence,
        "risk_complexity_rationale": "Die finale Freigabe verbleibt beim Menschen.",
        "risk_complexity_evidence_url": "https://example.invalid/risk",
        "overall_rationale": "Pilot ist mit klar begrenztem Scope vertretbar.",
    }


@pytest.mark.django_db
def test_assessment_is_versioned_and_syncs_current_ratings(
    client, coordinator, strategy_use_case
):
    client.force_login(coordinator)

    response = client.post(
        reverse("use_cases:assessment_create", args=[strategy_use_case.pk]),
        assessment_payload(),
    )

    assert response.status_code == 302
    assessment = DecisionAssessment.objects.get(use_case=strategy_use_case)
    assert assessment.version == 1
    assert assessment.minimum_confidence == DecisionAssessment.Confidence.HIGH

    strategy_use_case.refresh_from_db()
    assert strategy_use_case.business_value == UseCase.Level.HIGH
    assert strategy_use_case.risk_complexity == UseCase.Level.LOW

    response = client.post(
        reverse("use_cases:assessment_create", args=[strategy_use_case.pk]),
        assessment_payload(business_value=UseCase.Level.MEDIUM),
    )

    assert response.status_code == 302
    assert list(
        DecisionAssessment.objects.filter(use_case=strategy_use_case).values_list(
            "version", flat=True
        )
    ) == [2, 1]


@pytest.mark.django_db
def test_only_coordinator_can_create_assessment(client, owner, strategy_use_case):
    client.force_login(owner)

    response = client.get(
        reverse("use_cases:assessment_create", args=[strategy_use_case.pk])
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_benefit_measurement_updates_current_metric_snapshot(
    client, owner, strategy_use_case
):
    client.force_login(owner)
    measured_at = timezone.localdate()

    response = client.post(
        reverse("use_cases:benefit_measurement_create", args=[strategy_use_case.pk]),
        {
            "measured_at": measured_at,
            "period": "Pilotwochen 5 bis 8",
            "actual_value": "8.0",
            "method": "100 repräsentative Rechnungen",
            "evidence_url": "https://example.invalid/measurement",
            "variance_reason": "",
            "decision_consequence": "Go-live fachlich vorbereiten.",
        },
    )

    assert response.status_code == 302
    measurement = BenefitMeasurement.objects.get(use_case=strategy_use_case)
    assert measurement.result == UseCase.MetricResult.ACHIEVED

    strategy_use_case.refresh_from_db()
    assert strategy_use_case.metric_actual == Decimal("8.0000")
    assert strategy_use_case.metric_measured_at == measured_at
    assert strategy_use_case.realized_result == "Go-live fachlich vorbereiten."


@pytest.mark.django_db
def test_pilot_check_surfaces_missing_strategy_and_assessment(
    owner, coordinator, business_unit
):
    use_case = UseCase.objects.create(
        title="Assistent",
        problem_statement="Wissen ist verteilt.",
        business_unit=business_unit,
        affected_process="Auskunft",
        business_owner=owner,
        coordinator=coordinator,
        expected_benefit="Schnellere Antworten",
        data_sources="Wissensbasis",
        next_review_date=timezone.localdate(),
        planned_pilot_end=timezone.localdate() + timedelta(days=14),
        metric_name="Antwortzeit",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Minuten",
        metric_baseline=Decimal("30"),
        metric_target=Decimal("10"),
        metric_measurement_method="Zeitmessung bei 20 Anfragen",
    )

    check = check_pilot_start(use_case)

    assert "Kein strategisches Ziel verknüpft" in " ".join(check.warnings)
    assert "keine versionierte Bewertung" in " ".join(check.warnings)
