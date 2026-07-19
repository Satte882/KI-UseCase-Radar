import pytest
from django.urls import reverse
from django.utils import timezone
from ki_radar.governance.models import GovernanceAssessment
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(title="KI", problem_statement="Problem", business_unit=business_unit, affected_process="Prozess", business_owner=owner, expected_benefit="Nutzen")


@pytest.mark.django_db
def test_governance_updates_required_flags(client, coordinator, use_case):
    client.force_login(coordinator)
    response = client.post(reverse("governance:create", args=[use_case.pk]), {
        "assessment_date": timezone.localdate(), "basis_version": "2026-01",
        "personal_data": "on", "privacy_review_required": "on",
        "result": GovernanceAssessment.Result.PRIVACY, "rationale": "Personenbezogene Daten",
    })
    assert response.status_code == 302
    use_case.refresh_from_db()
    assert use_case.privacy_review_required is True
