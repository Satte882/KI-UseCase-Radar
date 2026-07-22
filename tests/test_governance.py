import pytest
from django import forms
from django.urls import reverse
from django.utils import timezone

from ki_radar.governance.forms import GovernanceAssessmentForm
from ki_radar.governance.models import GovernanceAssessment
from ki_radar.use_cases.forms import UseCaseForm
from ki_radar.use_cases.governance_status import build_governance_statuses
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(
        title="KI",
        problem_statement="Problem",
        business_unit=business_unit,
        affected_process="Prozess",
        business_owner=owner,
        expected_benefit="Nutzen",
    )


@pytest.mark.django_db
def test_governance_updates_required_flags(client, coordinator, use_case):
    client.force_login(coordinator)
    response = client.post(
        reverse("governance:create", args=[use_case.pk]),
        {
            "assessment_date": timezone.localdate(),
            "basis_version": "2026-01",
            "personal_data": "on",
            "privacy_review_required": "on",
            "result": GovernanceAssessment.Result.PRIVACY,
            "rationale": "Personenbezogene Daten",
        },
    )
    assert response.status_code == 302
    use_case.refresh_from_db()
    assert use_case.privacy_review_required is True


@pytest.mark.django_db
def test_governance_form_uses_german_labels():
    form = GovernanceAssessmentForm()

    assert form.fields["assessment_date"].label == "Screening-Datum"
    assert form.fields["basis_version"].label == "Prüfgrundlage / Version"
    assert form.fields["personal_data"].label == "Personenbezogene Daten"
    assert form.fields["result"].label == "Ergebnis"


def _assessment(use_case, reviewer, **requirements):
    return GovernanceAssessment.objects.create(
        use_case=use_case,
        assessment_date=timezone.localdate(),
        reviewer=reviewer,
        basis_version="2026-07",
        result=GovernanceAssessment.Result.NO_FLAGS,
        rationale="Aktuelles Screening",
        **requirements,
    )


def _edit_payload(use_case, **overrides):
    form = UseCaseForm(instance=use_case)
    payload = {}
    for name, field in form.fields.items():
        value = form.initial.get(name)
        if isinstance(field, forms.BooleanField):
            if value:
                payload[name] = "on"
        elif value is not None:
            payload[name] = getattr(value, "pk", value)
    payload.update(
        {
            "business_domain": "other",
            "business_capability": "Allgemeine Prozessunterstützung",
            "process_area": use_case.affected_process,
            **overrides,
        }
    )
    return payload


@pytest.mark.django_db
def test_governance_status_distinguishes_all_four_states(coordinator, use_case):
    statuses = {status.kind.key: status for status in build_governance_statuses(use_case)}
    assert {status.state for status in statuses.values()} == {"not_assessed"}

    _assessment(
        use_case,
        coordinator,
        security_review_required=True,
        legal_review_required=True,
    )
    use_case.security_review_required = True
    use_case.legal_review_required = True
    use_case.legal_review_completed = True
    use_case.save()

    statuses = {status.kind.key: status for status in build_governance_statuses(use_case)}
    assert statuses["privacy"].state == "not_required"
    assert statuses["security"].state == "open"
    assert statuses["legal"].state == "completed"
    assert statuses["privacy"].actor == coordinator.get_display_name()
    assert statuses["legal"].actor == "System"


@pytest.mark.django_db
def test_general_form_only_allows_required_reviews_to_be_completed(coordinator, use_case):
    _assessment(use_case, coordinator, privacy_review_required=True)
    use_case.privacy_review_required = True
    use_case.save(update_fields=["privacy_review_required", "updated_at"])

    form = UseCaseForm(instance=use_case, current_user=coordinator)

    assert "privacy_review_completed" in form.fields
    assert "security_review_completed" not in form.fields
    assert "legal_review_completed" not in form.fields


@pytest.mark.django_db
def test_manipulated_post_cannot_complete_unassessed_or_unrequired_review(client, owner, use_case):
    client.force_login(owner)
    response = client.post(
        reverse("use_cases:edit", args=[use_case.pk]),
        _edit_payload(use_case, privacy_review_completed="on"),
    )
    assert response.status_code == 302
    use_case.refresh_from_db()
    assert use_case.privacy_review_completed is False

    _assessment(use_case, owner, privacy_review_required=False)
    response = client.post(
        reverse("use_cases:edit", args=[use_case.pk]),
        _edit_payload(use_case, privacy_review_completed="on"),
    )
    assert response.status_code == 302
    use_case.refresh_from_db()
    assert use_case.privacy_review_completed is False


@pytest.mark.django_db
def test_required_review_completion_and_reopening_use_existing_history(
    client, owner, coordinator, use_case
):
    _assessment(use_case, coordinator, privacy_review_required=True)
    use_case.privacy_review_required = True
    use_case.save(update_fields=["privacy_review_required", "updated_at"])
    client.force_login(owner)

    completed = client.post(
        reverse("use_cases:edit", args=[use_case.pk]),
        _edit_payload(use_case, privacy_review_completed="on"),
    )
    assert completed.status_code == 302
    use_case.refresh_from_db()
    status = build_governance_statuses(use_case)[0]
    assert status.state == "completed"
    assert status.actor == owner.get_display_name()
    assert status.changed_at_has_time is True

    reopened_payload = _edit_payload(use_case)
    reopened_payload.pop("privacy_review_completed")
    reopened = client.post(
        reverse("use_cases:edit", args=[use_case.pk]),
        reopened_payload,
    )
    assert reopened.status_code == 302
    use_case.refresh_from_db()
    status = build_governance_statuses(use_case)[0]
    assert status.state == "open"
    assert status.actor == owner.get_display_name()
    assert status.attribution_note == "Zuletzt wieder geöffnet"


@pytest.mark.django_db
def test_new_screening_normalizes_obsolete_completion_atomically(client, coordinator, use_case):
    _assessment(use_case, coordinator, privacy_review_required=True)
    use_case.privacy_review_required = True
    use_case.privacy_review_completed = True
    use_case.save()
    client.force_login(coordinator)

    response = client.post(
        reverse("governance:create", args=[use_case.pk]),
        {
            "assessment_date": timezone.localdate(),
            "basis_version": "2026-08",
            "result": GovernanceAssessment.Result.NO_FLAGS,
            "rationale": "Datenschutzprüfung nicht mehr erforderlich",
        },
    )

    assert response.status_code == 302
    use_case.refresh_from_db()
    assert use_case.privacy_review_required is False
    assert use_case.privacy_review_completed is False
    assert use_case.governance_assessments.count() == 2
    assert build_governance_statuses(use_case)[0].state == "not_required"


@pytest.mark.django_db
def test_detail_shows_semantic_status_reviewer_and_screening_date(
    client, owner, coordinator, use_case
):
    _assessment(use_case, coordinator, privacy_review_required=True)
    use_case.privacy_review_required = True
    use_case.save(update_fields=["privacy_review_required", "updated_at"])
    client.force_login(owner)

    response = client.get(reverse("use_cases:detail", args=[use_case.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Noch nicht bewertet" not in content
    assert "Nicht erforderlich" in content
    assert "Offen" in content
    assert coordinator.get_display_name() in content
    assert timezone.localdate().strftime("%d.%m.%Y") in content


@pytest.mark.django_db
def test_legacy_completion_without_user_has_honest_fallback(coordinator, use_case):
    _assessment(use_case, coordinator, legal_review_required=True)
    use_case.legal_review_required = True
    use_case.legal_review_completed = True
    use_case.save()

    status = build_governance_statuses(use_case)[2]

    assert status.state == "completed"
    assert status.actor == "System"
