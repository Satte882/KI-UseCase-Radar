import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.governance.models import GovernanceAssessment
from ki_radar.reviews.models import Review
from ki_radar.reviews.services import create_review
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(
        title="Idee",
        problem_statement="Problem",
        business_unit=business_unit,
        affected_process="Prozess",
        business_owner=owner,
        expected_benefit="Nutzen",
    )


@pytest.mark.django_db
def test_only_coordinator_can_open_review_form(client, owner, coordinator, use_case):
    client.force_login(owner)
    assert client.get(reverse("reviews:create", args=[use_case.pk])).status_code == 403
    client.force_login(coordinator)
    assert client.get(reverse("reviews:create", args=[use_case.pk])).status_code == 200


@pytest.mark.django_db
def test_continue_review_keeps_status(client, coordinator, use_case):
    client.force_login(coordinator)
    response = client.post(
        reverse("reviews:create", args=[use_case.pk]),
        {
            "review_date": timezone.localdate(),
            "decision": Review.Decision.CONTINUE,
            "new_status": UseCase.Status.IDEA,
            "rationale": "Weiter prüfen",
            "open_actions": "",
            "action_owner": "",
            "action_due_date": "",
            "next_review_date": timezone.localdate(),
        },
    )
    assert response.status_code == 302
    assert Review.objects.count() == 1


@pytest.mark.django_db
def test_review_can_supply_required_review_date_for_pilot_transition(coordinator, use_case):
    today = timezone.localdate()
    use_case.baseline = "30 Minuten"
    use_case.success_criterion = "Unter 10 Minuten"
    use_case.target_value = "10 Minuten"
    use_case.data_sources = "Freigegebene Wissensbasis"
    use_case.planned_pilot_end = today
    use_case.save()
    GovernanceAssessment.objects.create(
        use_case=use_case,
        assessment_date=today,
        reviewer=coordinator,
        basis_version="2026-01",
        result=GovernanceAssessment.Result.NO_FLAGS,
        rationale="Keine besonderen Hinweise",
    )

    review = create_review(
        use_case=use_case,
        actor=coordinator,
        data={
            "review_date": today,
            "decision": Review.Decision.START_PILOT,
            "new_status": UseCase.Status.PILOT,
            "rationale": "Pilot ist fachlich vorbereitet",
            "open_actions": "",
            "action_owner": None,
            "action_due_date": None,
            "next_review_date": today,
        },
    )

    use_case.refresh_from_db()
    assert use_case.status == UseCase.Status.PILOT
    assert use_case.next_review_date == today
    assert use_case.history.first().history_user == coordinator
    assert review.history.first().history_user == coordinator
