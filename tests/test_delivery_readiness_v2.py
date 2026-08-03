import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from ki_radar.delivery.models import DeliverySectionReview
from ki_radar.delivery.readiness import evaluate_delivery_readiness
from ki_radar.delivery.services import (
    create_delivery_package,
    review_delivery_section,
)
from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase


def make_approved_use_case(*, owner, technical_owner, coordinator, business_unit):
    use_case = UseCase.objects.create(
        title="Automatische Lieferantenauswahl",
        summary="Angebote strukturiert vergleichen.",
        problem_statement="Uneinheitliche Angebote erzeugen Rückfragen.",
        business_unit=business_unit,
        affected_process="Lieferantenauswahl",
        target_users="Einkauf",
        submitter=owner,
        business_owner=owner,
        technical_owner=technical_owner,
        source_systems="ERP, Shared Inbox, Dateiablage",
        data_sources="Angebote und Kriterienkatalog",
        interface_description="Dateiimport und ERP-Export",
        intended_users="Strategischer Einkauf",
        intended_purpose="Angebote extrahieren und vergleichbar darstellen.",
        expected_benefit="Durchlaufzeit reduzieren.",
        metric_name="Durchlaufzeit",
        metric_type=UseCase.MetricType.DURATION,
        metric_direction=UseCase.MetricDirection.LOWER,
        metric_unit="Tage",
        metric_baseline=Decimal("5"),
        metric_target=Decimal("3"),
        metric_measurement_method="Median über zehn Vorgänge.",
        metric_measurement_period="Vier Wochen.",
        human_oversight="Einkauf prüft und entscheidet.",
        support_responsibility="Application Management",
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
        evidence_url="https://example.com/evidence",
        rationale="Repräsentative Messung und technische Vorprüfung liegen vor.",
        governance_precheck_completed=True,
        recommendation=UseCase.DecisionStatus.APPROVED,
    )
    ApprovalDecision.objects.create(
        use_case=use_case,
        assessment=assessment,
        decision_status=UseCase.DecisionStatus.APPROVED,
        rationale="Freigabe für Delivery.",
        decided_by=coordinator,
        governance_confirmed=True,
        finalized_at=timezone.now(),
    )
    return use_case


@pytest.mark.django_db
def test_package_creates_seven_reviews_with_source_manifest(
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )

    package = create_delivery_package(use_case=use_case, actor=coordinator)

    assert package.readiness_schema_version == 2
    assert package.section_reviews.count() == 7
    assert all(review.source_manifest for review in package.section_reviews.all())
    assert all(
        review.review_status == DeliverySectionReview.ReviewStatus.NEEDS_REVIEW
        for review in package.section_reviews.all()
    )


@pytest.mark.django_db
def test_solution_section_requires_business_and_technical_confirmation(
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm",
        actor=owner,
        note="Fachlich bestätigt.",
    )
    review = package.section_reviews.get(section_key="solution_direction")
    assert review.business_confirmed_by == owner
    assert review.technical_confirmed_by is None
    assert review.review_status == DeliverySectionReview.ReviewStatus.NEEDS_REVIEW

    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm",
        actor=other_owner,
        note="Technisch bestätigt.",
    )
    review.refresh_from_db()
    assert review.technical_confirmed_by == other_owner
    assert review.review_status == DeliverySectionReview.ReviewStatus.CONFIRMED


@pytest.mark.django_db
def test_generic_prefill_and_open_reviews_are_readiness_blockers(
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    findings = evaluate_delivery_readiness(package)
    codes = {finding.code for finding in findings}

    assert "SECTION_NEEDS_REVIEW" in codes
    assert "OUT_OF_SCOPE_GENERIC" in codes
    assert "SYSTEM_RESPONSIBILITIES_GENERIC" in codes


@pytest.mark.django_db
def test_not_applicable_requires_reason(
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    with pytest.raises(ValidationError, match="begründet"):
        review_delivery_section(
            package=package,
            section_key="architecture_and_data",
            action="not_applicable",
            actor=coordinator,
            note="",
        )


@pytest.mark.django_db
def test_methodology_page_and_download_use_same_complete_file(client, owner):
    client.force_login(owner)
    source_path = Path(settings.BASE_DIR) / "docs" / "DELIVERY_METHODOLOGY.md"
    source = source_path.read_text(encoding="utf-8")

    page = client.get(reverse("delivery:methodology_reference"))
    download = client.get(reverse("delivery:methodology_download"))

    assert page.status_code == 200
    assert "Vorgehensmodell für produktionsreife KI-Systeme" in page.content.decode()
    assert "Vorgehensmodell herunterladen" in page.content.decode()
    assert download.status_code == 200
    assert download["Content-Type"].startswith("text/markdown")
    assert "attachment;" in download["Content-Disposition"]
    assert (
        "KI-Radar_Vorgehensmodell_CRISP-MLQ_ML-Test-Score_v2.0.md"
        in download["Content-Disposition"]
    )
    assert download.content.decode() == source


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("### A. Daten", "### B. Modell"),
        ("### B. Modell", "### C. Infrastruktur"),
        ("### C. Infrastruktur", "### D. Monitoring"),
        ("### D. Monitoring", "Die Liste ist eine deutschsprachige"),
    ],
)
def test_methodology_contains_all_28_ml_test_score_checks(start, end):
    source = (Path(settings.BASE_DIR) / "docs" / "DELIVERY_METHODOLOGY.md").read_text(
        encoding="utf-8"
    )
    block = source.split(start, 1)[1].split(end, 1)[0]
    assert len(re.findall(r"^\d+\.", block, flags=re.MULTILINE)) == 7


def test_methodology_contains_all_24_sections_and_required_components():
    source = (Path(settings.BASE_DIR) / "docs" / "DELIVERY_METHODOLOGY.md").read_text(
        encoding="utf-8"
    )
    for section_number in range(1, 25):
        assert re.search(rf"^# {section_number}\. ", source, flags=re.MULTILINE)
    for marker in [
        "Konflikt- und Eskalationsverfahren",
        "Stufe A: Kompaktes Vorhaben",
        "Stufe B: Standardvorhaben",
        "Stufe C: Erweitertes Vorhaben",
        "Berechnung des ML Test Score",
        "Übertragung auf generative KI",
        "Quality-Gate-Protokoll",
    ]:
        assert marker in source


@pytest.mark.django_db
def test_package_detail_shows_methodology_actions(
    client,
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    client.force_login(coordinator)

    response = client.get(reverse("delivery:package_detail", kwargs={"pk": package.pk}))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Vorgehensmodell" in content
    assert "Vorgehensmodell herunterladen" in content
    assert reverse("delivery:methodology_reference") in content
    assert reverse("delivery:methodology_download") in content


@pytest.mark.django_db
def test_shared_section_requires_explicit_confirmation_role(
    owner, other_owner, coordinator, business_unit
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    with pytest.raises(ValidationError, match="ausdrücklich auswählen"):
        review_delivery_section(
            package=package,
            section_key="solution_direction",
            action="confirm",
            actor=coordinator,
        )


@pytest.mark.django_db
def test_authorized_substitutes_can_confirm_only_the_selected_role(
    owner, other_owner, coordinator, business_unit
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_business",
        actor=other_owner,
    )
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_technical",
        actor=coordinator,
    )

    review = package.section_reviews.get(section_key="solution_direction")
    assert review.business_confirmed_by == other_owner
    assert review.business_confirmation_role == "Berechtigte fachliche Stellvertretung"
    assert review.technical_confirmed_by == coordinator
    assert review.technical_confirmation_role == "Berechtigte technische Stellvertretung"
    assert review.review_status == DeliverySectionReview.ReviewStatus.CONFIRMED


@pytest.mark.django_db
def test_non_admin_cannot_confirm_both_roles(owner, other_owner, coordinator, business_unit):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_business",
        actor=coordinator,
    )

    with pytest.raises(ValidationError, match="Technischer Administrator"):
        review_delivery_section(
            package=package,
            section_key="solution_direction",
            action="confirm_technical",
            actor=coordinator,
            role_collapse_reason="Testdurchlauf.",
        )


@pytest.mark.django_db
def test_dual_owner_is_not_an_exception(owner, business_unit, coordinator):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_business",
        actor=owner,
    )

    with pytest.raises(ValidationError, match="Technischer Administrator"):
        review_delivery_section(
            package=package,
            section_key="solution_direction",
            action="confirm_technical",
            actor=owner,
            role_collapse_reason="Kleines Team.",
        )


@pytest.mark.django_db
def test_technical_admin_can_use_audited_same_person_exception(
    owner, other_owner, coordinator, technical_admin, business_unit
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_business",
        actor=technical_admin,
    )

    with pytest.raises(ValidationError, match="Admin-Sonderbestätigung"):
        review_delivery_section(
            package=package,
            section_key="solution_direction",
            action="confirm_technical",
            actor=technical_admin,
        )

    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_technical",
        actor=technical_admin,
        role_collapse_reason="Vollständiger administrativer Test des Delivery-Flows.",
    )
    review = package.section_reviews.get(section_key="solution_direction")

    assert review.admin_override_confirmed is True
    assert review.has_role_collapse is True
    assert review.review_status == DeliverySectionReview.ReviewStatus.CONFIRMED
    assert review.business_confirmation_role == "Admin-Sonderbestätigung"
    assert review.technical_confirmation_role == "Admin-Sonderbestätigung"
    assert review.role_collapse_reason.startswith("Vollständiger administrativer Test")


@pytest.mark.django_db
def test_delivery_page_labels_admin_override_by_confirmation_role(
    client, owner, other_owner, coordinator, technical_admin, business_unit
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_business",
        actor=technical_admin,
    )
    review_delivery_section(
        package=package,
        section_key="solution_direction",
        action="confirm_technical",
        actor=technical_admin,
        role_collapse_reason="Administrativer Ende-zu-Ende-Test.",
    )
    client.force_login(technical_admin)

    response = client.get(package.get_absolute_url())
    body = response.content.decode()

    assert response.status_code == 200
    assert f"Fachlich: {technical_admin} · Admin-Sonderbestätigung" in body
    assert f"Technisch: {technical_admin} · Admin-Sonderbestätigung" in body
    assert "Admin-Sonderbestätigung ohne Vier-Augen-Prinzip" in body
    assert "Administrativer Ende-zu-Ende-Test" in body

@pytest.mark.django_db
def test_delivery_uses_canonical_working_values_and_reports_field_level_source_change(
    owner,
    other_owner,
    coordinator,
    business_unit,
):
    use_case = make_approved_use_case(
        owner=owner,
        technical_owner=other_owner,
        coordinator=coordinator,
        business_unit=business_unit,
    )
    package = create_delivery_package(use_case=use_case, actor=coordinator)

    assert package.problem_context == use_case.problem_statement
    assert package.problem_context.count(use_case.problem_statement) == 1
    assert package.solution_outline == use_case.intended_purpose

    use_case.expected_benefit = "Durchlaufzeit und Rückfragen reduzieren."
    use_case.save(update_fields=["expected_benefit", "updated_at"])
    findings = evaluate_delivery_readiness(package)

    messages = [
        finding.message
        for finding in findings
        if finding.code == "SOURCE_CHANGED_AFTER_SNAPSHOT"
    ]
    assert any("Ziel und erwartetes Ergebnis" in message for message in messages)
    assert any("Durchlaufzeit und Rückfragen reduzieren" in message for message in messages)
