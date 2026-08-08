from decimal import Decimal

import pytest
from django.utils import timezone

from ki_radar.delivery.mapping_refresh import BLOCK8_MAPPING_MANIFEST_KEY, MappingStatus
from ki_radar.delivery.services import create_delivery_package, refresh_delivery_package_mapping
from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase


@pytest.fixture
def approved_use_case(owner, coordinator, business_unit):
    use_case = UseCase.objects.create(
        title="Assistierter Angebotsvergleich",
        summary="Angebote strukturiert vergleichen.",
        problem_statement="Uneinheitliche Angebote verlängern die Auswahl.",
        expected_benefit="Durchlaufzeit messbar reduzieren.",
        affected_process="Lieferantenauswahl",
        target_users="Einkauf",
        intended_users="Strategischer Einkauf",
        intended_purpose="Angebotsdaten vergleichbar darstellen.",
        source_systems="ERP und Dateiablage",
        data_sources="Angebote und Lieferantenstammdaten",
        interface_description="ERP-Export",
        human_oversight="Einkauf trifft die finale Entscheidung.",
        support_responsibility="IT Application Management",
        metric_name="Durchlaufzeit",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Tage",
        metric_baseline=Decimal("5"),
        metric_target=Decimal("3"),
        metric_measurement_method="Median über zehn Vorgänge",
        metric_measurement_period="Pilot",
        success_criterion="Zielwert im Pilot erreicht",
        business_unit=business_unit,
        submitter=owner,
        business_owner=owner,
        coordinator=coordinator,
        technical_owner=coordinator,
        status=UseCase.Status.REVIEW,
        decision_status=UseCase.DecisionStatus.APPROVED,
    )
    assessment = DecisionAssessment.objects.create(
        use_case=use_case,
        version=1,
        assessed_by=coordinator,
        business_value=UseCase.Level.HIGH,
        strategic_fit=UseCase.Level.HIGH,
        technical_feasibility=UseCase.Level.HIGH,
        data_readiness=UseCase.Level.MEDIUM,
        risk_complexity=UseCase.Level.MEDIUM,
        evidence_quality=DecisionAssessment.EvidenceQuality.REPRESENTATIVE,
        evidence_recency=DecisionAssessment.ConfidenceFactor.SOLID,
        evidence_coverage=DecisionAssessment.ConfidenceFactor.SOLID,
        independent_review=DecisionAssessment.ConfidenceFactor.SOLID,
        assumptions_resolved=DecisionAssessment.ConfidenceFactor.SOLID,
        rationale="Quellen sind geprüft.",
        governance_precheck_completed=True,
        recommendation=UseCase.DecisionStatus.APPROVED,
    )
    ApprovalDecision.objects.create(
        use_case=use_case,
        assessment=assessment,
        decision_status=UseCase.DecisionStatus.APPROVED,
        rationale="Delivery ist freigegeben.",
        decided_by=coordinator,
        governance_confirmed=True,
        finalized_at=timezone.now(),
    )
    return use_case


def test_existing_delivery_path_remains_explicit_fallback(approved_use_case, coordinator):
    package = create_delivery_package(
        use_case=approved_use_case,
        actor=coordinator,
        use_evidence_mapper=False,
    )

    assert "Kernablauf" in package.functional_requirements
    review = package.section_reviews.get(section_key="problem_and_target")
    assert BLOCK8_MAPPING_MANIFEST_KEY not in review.source_manifest


def test_new_package_can_use_grounded_block8_mapper(approved_use_case, coordinator):
    package = create_delivery_package(
        use_case=approved_use_case,
        actor=coordinator,
        use_evidence_mapper=True,
    )

    assert package.problem_context == "Uneinheitliche Angebote verlängern die Auswahl."
    assert package.target_outcome == "Durchlaufzeit messbar reduzieren."
    assert "Metrik: Durchlaufzeit" in package.measurement_plan
    assert "Erfolgskriterium: Zielwert im Pilot erreicht" in package.acceptance_criteria
    assert package.functional_requirements == ""
    assert package.non_functional_requirements == ""
    assert package.security_privacy_requirements == ""
    assert package.logging_and_audit == ""
    assert package.mvp_scope == ""
    assert package.test_scenarios == ""
    assert package.initial_backlog == ""

    artifacts = package.architecture_artifacts
    assert "Quellsysteme: ERP und Dateiablage" in artifacts.system_landscape
    assert "Datenquellen: Angebote und Lieferantenstammdaten" in artifacts.data_flows
    assert artifacts.system_responsibilities == ""
    assert artifacts.data_quality_and_access == ""
    assert artifacts.integration_contracts == ""
    assert artifacts.integration_operations == ""

    manifests = [review.source_manifest for review in package.section_reviews.all()]
    assert manifests
    assert all(BLOCK8_MAPPING_MANIFEST_KEY in manifest for manifest in manifests)


def test_explicit_refresh_updates_only_safe_changed_mapping(approved_use_case, coordinator):
    package = create_delivery_package(
        use_case=approved_use_case,
        actor=coordinator,
        use_evidence_mapper=True,
    )
    approved_use_case.problem_statement = "Neue bestätigte Problembeschreibung."
    approved_use_case.save(update_fields=["problem_statement", "updated_at"])

    plan = refresh_delivery_package_mapping(package)
    package.refresh_from_db()

    assert plan.changed_fields == ("problem_context",)
    assert package.problem_context == "Neue bestätigte Problembeschreibung."
    review = package.section_reviews.get(section_key="problem_and_target")
    entry = review.source_manifest[BLOCK8_MAPPING_MANIFEST_KEY]["fields"]["problem_context"]
    assert entry["status"] == MappingStatus.MAPPED
    assert entry["mapped_value"] == "Neue bestätigte Problembeschreibung."


def test_explicit_refresh_preserves_manual_divergence_as_conflict(approved_use_case, coordinator):
    package = create_delivery_package(
        use_case=approved_use_case,
        actor=coordinator,
        use_evidence_mapper=True,
    )
    package.problem_context = "Manuell präzisierter Delivery-Kontext."
    package.save(update_fields=["problem_context", "updated_at"])
    approved_use_case.problem_statement = "Neue bestätigte Problembeschreibung."
    approved_use_case.save(update_fields=["problem_statement", "updated_at"])

    plan = refresh_delivery_package_mapping(package)
    package.refresh_from_db()

    assert plan.changed_fields == ()
    assert plan.conflict_fields == ("problem_context",)
    assert package.problem_context == "Manuell präzisierter Delivery-Kontext."
    decision = next(item for item in plan.decisions if item.target_field == "problem_context")
    assert decision.status is MappingStatus.CONFLICT
    assert decision.conflict.previous_mapped_value == (
        "Uneinheitliche Angebote verlängern die Auswahl."
    )
    assert decision.conflict.current_value == "Manuell präzisierter Delivery-Kontext."
    assert decision.conflict.candidate_value == "Neue bestätigte Problembeschreibung."


def test_noop_refresh_is_idempotent_and_writes_no_delivery_fields(approved_use_case, coordinator):
    package = create_delivery_package(
        use_case=approved_use_case,
        actor=coordinator,
        use_evidence_mapper=True,
    )
    before_updated_at = package.updated_at

    first = refresh_delivery_package_mapping(package)
    package.refresh_from_db()
    after_first = package.updated_at
    second = refresh_delivery_package_mapping(package)
    package.refresh_from_db()

    assert first.changed_fields == ()
    assert second.changed_fields == ()
    assert after_first == before_updated_at
    assert package.updated_at == before_updated_at
