import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from ki_radar.architecture.models import UseCaseOrigin, ValueStream, ValueStreamStage
from ki_radar.use_cases.intake_views import SESSION_KEY, _persist_optional_origin
from ki_radar.use_cases.models import UseCase


@pytest.fixture
def value_stream(owner, business_unit):
    return ValueStream.objects.create(
        name="Beschaffung bis Zahlung",
        description="End-to-End-Wertschöpfung des Einkaufs.",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Freigegebener Bedarf",
        outcome="Bezahlte und verbuchte Leistung",
        scope="Vom Bedarf bis zur Zahlung",
        strategic_objective="Durchlaufzeit und Transparenz verbessern",
        stakeholders="Einkauf, Fachbereich, Finanzen",
        constraints="Bestehendes ERP bleibt führend",
        status=ValueStream.Status.ACTIVE,
    )


@pytest.fixture
def value_stream_stage(value_stream):
    return ValueStreamStage.objects.create(
        value_stream=value_stream,
        sequence=1,
        name="Lieferantenauswahl",
        description="Angebote einholen, vergleichen und Entscheidung vorbereiten.",
        actors="Einkauf und Fachbereich",
        systems="ERP, E-Mail, Dateiablage",
        documents="Angebote und Kriterienkatalog",
        pain_points="Angebote sind uneinheitlich und der Vergleich dauert zu lange.",
        baseline_metrics="Durchlaufzeit heute fünf Tage",
    )


@pytest.mark.django_db
def test_value_stream_is_optional_and_visible_to_authenticated_users(client, reader):
    client.force_login(reader)

    response = client.get(reverse("architecture:value_stream_list"))
    create_response = client.get(reverse("architecture:value_stream_create"))

    assert response.status_code == 200
    assert "Optionaler Discovery-Pfad" in response.content.decode()
    assert create_response.status_code == 403


@pytest.mark.django_db
def test_business_owner_can_create_value_stream(client, owner, business_unit):
    client.force_login(owner)

    response = client.post(
        reverse("architecture:value_stream_create"),
        {
            "name": "Order to Cash",
            "business_unit": business_unit.pk,
            "owner": "",
            "status": ValueStream.Status.DRAFT,
            "description": "Auftrag bis Zahlung",
            "trigger": "Kundenauftrag",
            "outcome": "Zahlungseingang",
            "scope": "Von Auftragseingang bis Zahlung",
            "strategic_objective": "Cash Conversion verbessern",
            "stakeholders": "Vertrieb, Operations, Finance",
            "constraints": "ERP bleibt führend",
        },
    )

    stream = ValueStream.objects.get(name="Order to Cash")
    assert response.status_code == 302
    assert stream.owner == owner
    assert stream.created_by == owner


@pytest.mark.django_db
def test_stage_can_prefill_existing_intake_without_bypassing_it(
    client,
    owner,
    value_stream_stage,
):
    client.force_login(owner)

    response = client.get(
        reverse(
            "architecture:stage_start_use_case", kwargs={"pk": value_stream_stage.pk}
        )
    )

    assert response.status_code == 302
    assert response.url == reverse("use_cases:create")
    stored = client.session[SESSION_KEY]
    assert stored["business_unit"] == value_stream_stage.value_stream.business_unit_id
    assert stored["affected_process"] == value_stream_stage.name
    assert stored["problem_statement"] == value_stream_stage.pain_points
    assert stored["source_stage_id"] == str(value_stream_stage.pk)


@pytest.mark.django_db
def test_optional_origin_is_persisted_only_for_valid_stage(
    owner,
    business_unit,
    value_stream_stage,
):
    use_case = UseCase.objects.create(
        title="Angebote vergleichbar machen",
        problem_statement="Uneinheitliche Angebote erschweren die Auswahl.",
        business_unit=business_unit,
        affected_process="Lieferantenauswahl",
        business_owner=owner,
        submitter=owner,
        expected_benefit="Durchlaufzeit reduzieren",
    )

    _persist_optional_origin(
        candidate=use_case,
        stored={"source_stage_id": str(value_stream_stage.pk)},
    )

    origin = UseCaseOrigin.objects.get(use_case=use_case)
    assert origin.stage == value_stream_stage

    direct_use_case = UseCase.objects.create(
        title="Direkt erfasster Use Case",
        problem_statement="Ein anderer fachlicher Bedarf.",
        business_unit=business_unit,
        affected_process="Direkter Prozess",
        business_owner=owner,
        submitter=owner,
        expected_benefit="Qualität verbessern",
    )
    _persist_optional_origin(candidate=direct_use_case, stored={})
    with pytest.raises(ObjectDoesNotExist):
        _ = direct_use_case.architecture_origin


@pytest.mark.django_db
def test_value_stream_detail_shows_traceable_use_case_origin(
    client,
    owner,
    business_unit,
    value_stream,
    value_stream_stage,
):
    use_case = UseCase.objects.create(
        title="Angebotsvergleich unterstützen",
        problem_statement="Vergleich ist manuell und langsam.",
        business_unit=business_unit,
        affected_process="Lieferantenauswahl",
        business_owner=owner,
        submitter=owner,
        expected_benefit="Bearbeitungszeit reduzieren",
    )
    UseCaseOrigin.objects.create(use_case=use_case, stage=value_stream_stage)
    client.force_login(owner)

    response = client.get(value_stream.get_absolute_url())

    assert response.status_code == 200
    content = response.content.decode()
    assert "End-to-End-Phasen" in content
    assert use_case.short_id in content
    assert "Use Case aus Phase ableiten" in content
