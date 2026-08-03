import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from ki_radar.delivery.models import DeliveryRoleSourceDecision, DeliverySectionReview
from ki_radar.delivery.readiness import evaluate_delivery_readiness
from ki_radar.delivery.services import (
    create_delivery_package,
    render_delivery_markdown,
    resolve_technical_owner_source_change,
    review_delivery_section,
)
from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase


def make_approved_use_case(*, owner, technical_owner, coordinator, business_unit):
    use_case = UseCase.objects.create(
        title="Automatische Lieferantenauswahl",
        summary="Angebote strukturiert vergleichen.",
        problem_statement="Uneinheitliche Angebote erzeugen RÃ¼ckfragen.",
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
        metric_measurement_method="Median Ã¼ber zehn VorgÃ¤nge.",
        metric_measurement_period="Vier Wochen.",
        human_oversight="Einkauf prÃ¼ft und entscheidet.",
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
        rationale="ReprÃ¤sentative Messung und technische VorprÃ¼fung liegen vor.",
        governance_precheck_completed=True,
        recommendation=UseCase.DecisionStatus.APPROVED,
    )
    ApprovalDecision.objects.create(
        use_case=use_case,
        assessment=assessment,
        decision_status=UseCase.DecisionStatus.APPROVED,
        rationale="Freigabe fÃ¼r Delivery.",
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
        note="Fachlich bestÃ¤tigt.",
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
        note="Technisch bestÃ¤tigt.",
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
    assert "OUT_OF_SCOPE_MISSING" in codes
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

    with pytest.raises(ValidationError, match="begrÃ¼ndet"):
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
    assert "Vorgehensmodell fÃ¼r produktionsreife KI-Systeme" in page.content.decode()
    assert "Vorgehensmodell herunterladen" in page.content.decode()
    assert download.status_code == 200
    assert download["Content-Type"].startswith("text/markdown")
    assert "attachment;" in download["Content-Disposition"]
    assert (
        "KI-Radar_Vorgehensmodell_CRISP-MLQ_ML-Test-Score_v2.0.md"
        in download["Content-Disposition"]
    )
    assert download.content.dec²È="24õ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤((€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½Ñ¡•É}½İ¹•È(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤((€€€™¥¹‘¥¹Ì€ô•Ù…±Õ…Ñ•}‘•±¥Ù•Éå}É•…‘¥¹•ÍÌ¡Á…­…”¤(€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½Ñ¡•É}½İ¹•È(€€€…ÍÍ•ÉĞ…¹ä (€€€€€€€™¥¹‘¥¹œ¹½‘”€ôô€‰Q!9%1}=]9I}M=UI}!9}U9IM=1Yˆ…¹™¥¹‘¥¹œ¹Í•Ù•É¥Ñä€ôô€‰‰±½­•Èˆ(€€€€€€€™½È™¥¹‘¥¹œ¥¸™¥¹‘¥¹Ì(€€€€¤(()ÁåÑ•ÍĞ¹µ…É¬¹‘©…¹½}‘ˆ)‘•˜Ñ•ÍÑ}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹•}…¹}‰•}…‘½ÁÑ•‘}İ¥Ñ¡}…Õ‘¥Ñ}‘•¥Í¥½¸ (€€€½İ¹•È°½Ñ¡•É}½İ¹•È°½½É‘¥¹…Ñ½È°‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ(¤è(€€€ÕÍ•}…Í”€ôµ…­•}…ÁÁÉ½Ù•‘}ÕÍ•}…Í” (€€€€€€€½İ¹•Èõ½İ¹•È°(€€€€€€€Ñ•¡¹¥…±}½İ¹•Èõ½Ñ¡•É}½İ¹•È°(€€€€€€€½½É‘¥¹…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğõ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤(€€€É•Ù¥•İ}‘•±¥Ù•Éå}Í•Ñ¥½¸ (€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€Í•Ñ¥½¹}­•äô‰…É¡¥Ñ•ÑÕÉ•}…¹‘}‘…Ñ„ˆ°(€€€€€€€…Ñ¥½¸ô‰½¹™¥Éµ}Ñ•¡¹¥…°ˆ°(€€€€€€€…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤((€€€‘•¥Í¥½¸€ôÉ•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€…Ñ¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€É…Ñ¥½¹…±”ô‰¥”Ñ•¡¹¥Í¡”Y•É…¹Ñİ½ÉÑÕ¹œİÕÉ‘”½É…¹¥Í…Ñ½É¥Í ¹•ÔéÕ•½É‘¹•Ğ¸ˆ°(€€€€€€€…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€¤((€€€Á…­…”¹É•™É•Í¡}™É½µ}‘ˆ ¤(€€€É•Ù¥•Ü€ôÁ…­…”¹Í•Ñ¥½¹}É•Ù¥•İÌ¹•Ğ¡Í•Ñ¥½¹}­•äô‰…É¡¥Ñ•ÑÕÉ•}…¹‘}‘…Ñ„ˆ¤(€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½İ¹•È(€€€…ÍÍ•ÉĞ‘•¥Í¥½¸¹½±‘}Ù…±Õ•}¥€ôôÍÑÈ¡½Ñ¡•É}½İ¹•È¹Á¬¤(€€€…ÍÍ•ÉĞ‘•¥Í¥½¸¹¹•İ}Ù…±Õ•}¥€ôôÍÑÈ¡½İ¹•È¹Á¬¤(€€€…ÍÍ•ÉĞ‘•¥Í¥½¸¹‘•¥‘•‘}‰ä€ôô½½É‘¥¹…Ñ½È(€€€‘•¥Í¥½¸¹É…Ñ¥½¹…±”€ô€‰9…¡ÑË‘±¥ Ù•Ë‘¹‘•ÉĞˆ(€€€İ¥Ñ ÁåÑ•ÍĞ¹É…¥Í•Ì¡Y…±¥‘…Ñ¥½¹ÉÉ½È°µ…Ñ ô‰EÕ•±±•¹•¹ÑÍ¡•¥‘Õ¹œ¥ÍĞÕ¹Ù•Ë‘¹‘•É±¥ ˆ¤è(€€€€€€€‘•¥Í¥½¸¹Í…Ù” ¤(€€€İ¥Ñ ÁåÑ•ÍĞ¹É…¥Í•Ì¡Y…±¥‘…Ñ¥½¹ÉÉ½È°µ…Ñ ô‰EÕ•±±•¹•¹ÑÍ¡•¥‘Õ¹œ¥ÍĞÕ¹Ù•Ë‘¹‘•É±¥ ˆ¤è(€€€€€€€‘•¥Í¥½¸¹‘•±•Ñ” ¤(€€€…ÍÍ•ÉĞÉ•Ù¥•Ü¹É•Ù¥•İ}ÍÑ…ÑÕÌ€ôô•±¥Ù•ÉåM•Ñ¥½¹I•Ù¥•Ü¹I•Ù¥•İMÑ…ÑÕÌ¹9M}IY%\(€€€…ÍÍ•ÉĞ¹½Ğ…¹ä (€€€€€€€™¥¹‘¥¹œ¹½‘”€ôô€‰Q!9%1}=]9I}M=UI}!9}U9IM=1Yˆ(€€€€€€€™½È™¥¹‘¥¹œ¥¸•Ù…±Õ…Ñ•}‘•±¥Ù•Éå}É•…‘¥¹•ÍÌ¡Á…­…”¤(€€€€¤(€€€•áÁ½ÉĞ€ôÉ•¹‘•É}‘•±¥Ù•Éå}µ…É­‘½İ¸¡Á…­…”¤(€€€…ÍÍ•ÉĞ€‰EÕ•±±•¹•¹ÑÍ¡•¥‘Õ¹•¸ˆ¥¸•áÁ½ÉĞ(€€€…ÍÍ•ÉĞ€‰¥”Ñ•¡¹¥Í¡”Y•É…¹Ñİ½ÉÑÕ¹œİÕÉ‘”½É…¹¥Í…Ñ½É¥Í ¹•ÔéÕ•½É‘¹•Ğ¸ˆ¥¸•áÁ½ÉĞ(()ÁåÑ•ÍĞ¹µ…É¬¹‘©…¹½}‘ˆ)‘•˜Ñ•ÍÑ}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹•}…¹}‰•}­•ÁÑ}…¹‘}¡…¹‘½Ù•É}Ù•ÉÍ¥½¹}¥Í}¥µµÕÑ…‰±” (€€€½İ¹•È°½Ñ¡•É}½İ¹•È°½½É‘¥¹…Ñ½È°‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ(¤è(€€€ÕÍ•}…Í”€ôµ…­•}…ÁÁÉ½Ù•‘}ÕÍ•}…Í” (€€€€€€€½İ¹•Èõ½İ¹•È°(€€€€€€€Ñ•¡¹¥…±}½İ¹•Èõ½Ñ¡•É}½İ¹•È°(€€€€€€€½½É‘¥¹…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğõ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤((€€€‘•¥Í¥½¸€ôÉ•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€…Ñ¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹-A}A-°(€€€€€€€É…Ñ¥½¹…±”ô‰¥”‰•ÍÑ•¡•¹‘”A…­…”µiÕ½É‘¹Õ¹œ‰±•¥‰Ğ›ñÈ‘¥•Í”Y•ÉÍ¥½¸Ù•É…¹Ñİ½ÉÑ±¥ ¸ˆ°(€€€€€€€…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€¤(€€€Á…­…”¹É•™É•Í¡}™É½µ}‘ˆ ¤(€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½Ñ¡•É}½İ¹•È(€€€…ÍÍ•ÉĞ‘•¥Í¥½¸¹‘•¥Í¥½¸€ôô•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹-A}A-(€€€…ÍÍ•ÉĞ¹½Ğ…¹ä (€€€€€€€™¥¹‘¥¹œ¹½‘”€ôô€‰Q!9%1}=]9I}M=UI}!9}U9IM=1Yˆ(€€€€€€€™½È™¥¹‘¥¹œ¥¸•Ù…±Õ…Ñ•}‘•±¥Ù•Éå}É•…‘¥¹•ÍÌ¡Á…­…”¤(€€€€¤((€€€Á…­…”¹ÍÑ…ÑÕÌ€ôÁ…­…”¹MÑ…ÑÕÌ¹!9}=YH(€€€Á…­…”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰ÍÑ…ÑÕÌˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½½É‘¥¹…Ñ½È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤(€€€İ¥Ñ ÁåÑ•ÍĞ¹É…¥Í•Ì¡Y…±¥‘…Ñ¥½¹ÉÉ½È°µ…Ñ ô‰Õ¹Ù•Ë‘¹‘•É±¥ ˆ¤è(€€€€€€€É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€€€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€€€€€…Ñ¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€€€€€É…Ñ¥½¹…±”ô‰…É˜¹… ƒq‰•É…‰”¹¥¡Ğµ•¡È•É™½±•¸¸ˆ°(€€€€€€€€€€€…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€€¤(()ÁåÑ•ÍĞ¹µ…É¬¹‘©…¹½}‘ˆ)‘•˜Ñ•ÍÑ}‘¥É•Ñ±å}¥¹Ù½±Ù•‘}½İ¹•ÉÍ}…¹}É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€½İ¹•È°½Ñ¡•É}½İ¹•È°½½É‘¥¹…Ñ½È°‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ(¤è(€€€ÕÍ•}…Í”€ôµ…­•}…ÁÁÉ½Ù•‘}ÕÍ•}…Í” (€€€€€€€½İ¹•Èõ½İ¹•È°(€€€€€€€Ñ•¡¹¥…±}½İ¹•Èõ½Ñ¡•É}½İ¹•È°(€€€€€€€½½É‘¥¹…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğõ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤((€€€‘•¥Í¥½¸€ôÉ•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€…Ñ¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€É…Ñ¥½¹…±”ô‰•È¹•Õ”Q•¡¹¥…°=İ¹•Èƒñ‰•É¹¥µµĞ‘¥”…­ÑÕ•±±”A…­…”µY•ÉÍ¥½¸¸ˆ°(€€€€€€€…Ñ½Èõ½İ¹•È°(€€€€¤((€€€Á…­…”¹É•™É•Í¡}™É½µ}‘ˆ ¤(€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½İ¹•È(€€€…ÍÍ•ÉĞ‘•¥Í¥½¸¹‘•¥‘•‘}‰ä€ôô½İ¹•È(()ÁåÑ•ÍĞ¹µ…É¬¹‘©…¹½}‘ˆ)‘•˜Ñ•ÍÑ}Õ¹É•±…Ñ•‘}ÕÍ•É}…¹¹½Ñ}É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€½İ¹•È°½Ñ¡•É}½İ¹•È°½½É‘¥¹…Ñ½È°‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°‘©…¹½}ÕÍ•É}µ½‘•°(¤è(€€€ÕÍ•}…Í”€ôµ…­•}…ÁÁÉ½Ù•‘}ÕÍ•}…Í” (€€€€€€€½İ¹•Èõ½İ¹•È°(€€€€€€€Ñ•¡¹¥…±}½İ¹•Èõ½Ñ¡•É}½İ¹•È°(€€€€€€€½½É‘¥¹…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğõ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤(€€€Õ¹É•±…Ñ•€ô‘©…¹½}ÕÍ•É}µ½‘•°¹½‰©•ÑÌ¹É•…Ñ•}ÕÍ•È¡ÕÍ•É¹…µ”ô‰Õ¹É•±…Ñ•µÉ½±”µ‘•¥‘•Èˆ¤((€€€İ¥Ñ ÁåÑ•ÍĞ¹É…¥Í•Ì¡Y…±¥‘…Ñ¥½¹ÉÉ½È°µ…Ñ ô‰™•¡±Ğ‘¥”	•É•¡Ñ¥Õ¹œˆ¤è(€€€€€€€É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹” (€€€€€€€€€€€Á…­…”õÁ…­…”°(€€€€€€€€€€€…Ñ¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€€€€€É…Ñ¥½¹…±”ô‰U¹‰•É•¡Ñ¥Ñ•Èƒq‰•É¹…¡µ•Ù•ÉÍÕ ¸ˆ°(€€€€€€€€€€€…Ñ½ÈõÕ¹É•±…Ñ•°(€€€€€€€€¤(()ÁåÑ•ÍĞ¹µ…É¬¹‘©…¹½}‘ˆ)‘•˜Ñ•ÍÑ}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ•}¡…¹•}¥Í}Ù¥Í¥‰±•}…¹‘}É•Í½±Ù…‰±•}¥¹}‘•±¥Ù•Éå}Õ¤ (€€€±¥•¹Ğ°(€€€½İ¹•È°(€€€½Ñ¡•É}½İ¹•È°(€€€½½É‘¥¹…Ñ½È°(€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(¤è(€€€ÕÍ•}…Í”€ôµ…­•}…ÁÁÉ½Ù•‘}ÕÍ•}…Í” (€€€€€€€½İ¹•Èõ½İ¹•È°(€€€€€€€Ñ•¡¹¥…±}½İ¹•Èõ½Ñ¡•É}½İ¹•È°(€€€€€€€½½É‘¥¹…Ñ½Èõ½½É‘¥¹…Ñ½È°(€€€€€€€‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğõ‰ÕÍ¥¹•ÍÍ}Õ¹¥Ğ°(€€€€¤(€€€Á…­…”€ôÉ•…Ñ•}‘•±¥Ù•Éå}Á…­…”¡ÕÍ•}…Í”õÕÍ•}…Í”°…Ñ½Èõ½½É‘¥¹…Ñ½È¤(€€€ÕÍ•}…Í”¹Ñ•¡¹¥…±}½İ¹•È€ô½İ¹•È(€€€ÕÍ•}…Í”¹Í…Ù”¡ÕÁ‘…Ñ•}™¥•±‘Ìõl‰Ñ•¡¹¥…±}½İ¹•Èˆ°€‰ÕÁ‘…Ñ•‘}…Ğ‰t¤(€€€±¥•¹Ğ¹™½É•}±½¥¸¡½½É‘¥¹…Ñ½È¤((€€€É•ÍÁ½¹Í”€ô±¥•¹Ğ¹•Ğ¡É•Ù•ÉÍ” ‰‘•±¥Ù•ÉäéÁ…­…•}‘•Ñ…¥°ˆ°­İ…ÉÌõì‰Á¬ˆèÁ…­…”¹Á­ô¤¤(€€€½¹Ñ•¹Ğ€ôÉ•ÍÁ½¹Í”¹½¹Ñ•¹Ğ¹‘•½‘” ¤(€€€…ÍÍ•ÉĞÉ•ÍÁ½¹Í”¹ÍÑ…ÑÕÍ}½‘”€ôô€ÈÀÀ(€€€…ÍÍ•ÉĞ€‰=™™•¹”‰İ•¥¡Õ¹œˆ¥¸½¹Ñ•¹Ğ(€€€…ÍÍ•ÉĞÍÑÈ¡½Ñ¡•É}½İ¹•È¤¥¸½¹Ñ•¹Ğ(€€€…ÍÍ•ÉĞÍÑÈ¡½İ¹•È¤¥¸½¹Ñ•¹Ğ(€€€…ÍÍ•ÉĞ€ (€€€€€€€É•Ù•ÉÍ” ‰‘•±¥Ù•ÉäéÁ…­…•}É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ”ˆ°­İ…ÉÌõì‰Á¬ˆèÁ…­…”¹Á­ô¤(€€€€€€€¥¸½¹Ñ•¹Ğ(€€€€¤((€€€É•ÍÁ½¹Í”€ô±¥•¹Ğ¹Á½ÍĞ (€€€€€€€É•Ù•ÉÍ” ‰‘•±¥Ù•ÉäéÁ…­…•}É•Í½±Ù•}Ñ•¡¹¥…±}½İ¹•É}Í½ÕÉ”ˆ°­İ…ÉÌõì‰Á¬ˆèÁ…­…”¹Á­ô¤°(€€€€€€€ì(€€€€€€€€€€€€‰…Ñ¥½¸ˆè•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€€€€€€‰É…Ñ¥½¹…±”ˆè€‰¥”¹•Õ”Ñ•¡¹¥Í¡”Y•É…¹Ñİ½ÉÑÕ¹œ¥±Ğ›ñÈ‘¥”…­ÑÕ•±±”A…­…”µY•ÉÍ¥½¸¸ˆ°(€€€€€€€ô°(€€€€¤((€€€…ÍÍ•ÉĞÉ•ÍÁ½¹Í”¹ÍÑ…ÑÕÍ}½‘”€ôô€ÌÀÈ(€€€Á…­…”¹É•™É•Í¡}™É½µ}‘ˆ ¤(€€€…ÍÍ•ÉĞÁ…­…”¹Ñ•¡¹¥…±}½İ¹•È€ôô½İ¹•È(€€€…ÍÍ•ÉĞÁ…­…”¹É½±•}Í½ÕÉ•}‘•¥Í¥½¹Ì¹™¥±Ñ•È (€€€€€€€‘•¥Í¥½¸õ•±¥Ù•ÉåI½±•M½ÕÉ••¥Í¥½¸¹•¥Í¥½¸¹=AQ}M=UI°(€€€€€€€‘•¥‘•‘}‰äõ½½É‘¥¹…Ñ½È°(€€€€¤¹•á¥ÍÑÌ ¤(