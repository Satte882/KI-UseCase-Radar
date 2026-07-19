import pytest
from django.urls import reverse
from django.utils import timezone
from ki_radar.reviews.models import Review
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(title="Idee", problem_statement="Problem", business_unit=business_unit, affected_process="Prozess", business_owner=owner, expected_benefit="Nutzen")


@pytest.mark.django_db
def test_only_coordinator_can_open_review_form(client, owner, coordinator, use_case):
    client.force_login(owner)
    assert client.get(reverse("reviews:create", args=[use_case.pk])).status_code == 403
    client.force_login(coordinator)
    assert client.get(reverse("reviews:create", args=[use_case.pk])).status_code == 200


@pytest.mark.django_db
def test_continue_review_keeps_status(client, coordinator, use_case):
    client.force_login(coordinator)
    response = client.post(reverse("reviews:create", args=[use_case.pk]), {
        "review_date": timezone.localdate(), "decision": Review.Decision.CONTINUE,
        "new_status": UseCase.Status.IDEA, "rationale": "Weiter prüfen", "open_actions": "",
        "action_owner": "", "action_due_date": "", "next_review_date": timezone.localdate(),
    })
    assert response.status_code == 302
    assert Review.objects.count() == 1
