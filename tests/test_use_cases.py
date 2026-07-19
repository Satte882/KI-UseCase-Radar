import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.use_cases.forms import UseCaseForm
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def use_case(owner, business_unit):
    return UseCase.objects.create(
        title="Dokumente klassifizieren",
        problem_statement="Manuelle Klassifizierung kostet Zeit.",
        business_unit=business_unit,
        affected_process="Dokumentenbearbeitung",
        submitter=owner,
        business_owner=owner,
        expected_benefit="Bearbeitungszeit reduzieren",
    )


@pytest.mark.django_db
def test_owner_can_edit_own_use_case(client, owner, use_case):
    client.force_login(owner)
    response = client.get(reverse("use_cases:edit", args=[use_case.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_owner_cannot_edit_foreign_use_case(client, other_owner, use_case):
    client.force_login(other_owner)
    response = client.get(reverse("use_cases:edit", args=[use_case.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_reader_cannot_create(client, reader):
    client.force_login(reader)
    assert client.get(reverse("use_cases:create")).status_code == 403


@pytest.mark.django_db
def test_use_case_form_uses_german_decision_labels():
    form = UseCaseForm()

    assert form.fields["problem_statement"].label == "Problemstellung"
    assert form.fields["next_review_date"].label == "Nächster Entscheidungstermin"
    assert form.fields["planned_pilot_end"].label == "Geplantes Pilotende"
    assert form.fields["technical_owner"].label == "Technischer Owner"


@pytest.mark.django_db
def test_use_case_form_renders_date_inputs_in_browser_format(use_case):
    localized_today = timezone.localdate().strftime("%d.%m.%Y")
    use_case.next_review_date = timezone.localdate()
    form = UseCaseForm(instance=use_case)

    assert f'value="{timezone.localdate().isoformat()}"' in form.as_p()
    assert localized_today not in form.as_p()


@pytest.mark.django_db
def test_history_tracks_user(client, owner, use_case):
    client.force_login(owner)
    use_case.title = "Geänderter Titel"
    use_case.save()
    latest = use_case.history.first()
    assert latest.title == "Geänderter Titel"


@pytest.mark.django_db
def test_csv_export_is_authenticated(client, owner, use_case):
    client.force_login(owner)
    response = client.get(reverse("use_cases:export_csv"))
    assert response.status_code == 200
    assert use_case.short_id in response.content.decode("utf-8-sig")
