from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ki_radar.accelerator.models import SolutionGenerationRun
from ki_radar.accelerator.solution_generation_contract import (
    GENERATED_OPTION_FIELDS,
    GENERATION_PROMPT_VERSION,
    GENERATION_SCHEMA_VERSION,
    OPTION_LANES,
)
from ki_radar.accelerator.solution_generation_sources import (
    build_solution_generation_source_context,
)
from ki_radar.architecture.focus import ValueStreamFocus
from ki_radar.architecture.models import (
    ProcessAnalysis,
    SolutionOption,
    SolutionSelectionDecision,
    ValueStream,
    ValueStreamStage,
)
from ki_radar.core.taxonomy import BusinessDomain, ScreeningLevel

LANE_NAMES = {
    "organizational": "Organisatorischer Entwurf",
    "rule_automation": "Regelbasierter Entwurf",
    "assistant": "Assistenzentwurf",
}


def make_process(owner, business_unit):
    stream = ValueStream.objects.create(
        name="Beschaffung bis Zahlung",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Freigegebener Bedarf",
        outcome="Bestellung ausgelöst",
        scope_in="Bedarf bis Bestellung",
        strategic_objective="Durchlaufzeit reduzieren",
        constraints="EU-Datenhaltung und menschliche Freigabe",
    )
    stage = ValueStreamStage.objects.create(
        value_stream=stream,
        sequence=2,
        name="Angebote vergleichen",
        description="Angebote fachlich vergleichen",
        actors="Einkauf",
        systems="ERP",
        documents="Angebote",
        pain_points="Manueller Vergleich",
        baseline_metrics="Elf Minuten pro Vergleich",
    )
    return ProcessAnalysis.objects.create(
        stage=stage,
        name="Angebotsvergleich",
        scope_start="Angebote liegen vor",
        scope_end="Auswahl ist dokumentiert",
        trigger="Angebotsfrist endet",
        outcome="Nachvollziehbare Auswahl",
        current_flow="Angebote werden manuell gegenübergestellt.",
        roles="Einkauf und Fachbereich",
        systems="ERP und Dateiablage",
        data_objects="Angebote und Kriterienkatalog",
        business_rules="Vier-Augen-Prinzip bei Freigabe",
        handoffs="Einkauf übergibt an Fachbereich",
        bottlenecks="Manuelle Übertragung verursacht Wartezeit.",
        exceptions="Fehlende Pflichtangaben werden nachgefordert.",
        baseline_metrics="Elf Minuten pro Vergleich",
        target_state_principles="Nachvollziehbar und assistierend",
        analyzed_by=owner,
    )


def select_focus(process, owner):
    ValueStreamFocus.objects.create(
        value_stream=process.stage.value_stream,
        business_domain=BusinessDomain.PROCUREMENT,
        capability="Supplier Sourcing und Angebotsvergleich",
        strategic_impact=ScreeningLevel.HIGH,
        economic_potential=ScreeningLevel.MEDIUM,
        pain_intensity=ScreeningLevel.HIGH,
        data_accessibility=ScreeningLevel.MEDIUM,
        change_effort=ScreeningLevel.MEDIUM,
        status=ValueStreamFocus.Status.SELECTED,
        rationale="Der Angebotsvergleich wurde für den Deep Dive ausgewählt.",
        updated_by=owner,
    )


def statement(text):
    return {
        "text": text,
        "source_ids": ["process.current_flow"],
        "assumptions": [],
        "open_evidence": [],
        "uncertainty": {
            "level": "low",
            "reason": "Direkt aus dem dokumentierten Ist-Ablauf abgeleitet.",
        },
    }


def make_run(owner, process):
    context = build_solution_generation_source_context(process)
    options = {
        lane: {
            field_name: statement(f"{LANE_NAMES[lane]} - {field_name}")
            for field_name in GENERATED_OPTION_FIELDS
        }
        for lane in OPTION_LANES
    }
    return SolutionGenerationRun.objects.create(
        process_analysis=process,
        process_version=process.version,
        source_hash=context.source_hash,
        requested_by=owner,
        status=SolutionGenerationRun.Status.SUCCESS,
        prompt_version=GENERATION_PROMPT_VERSION,
        generation_schema_version=GENERATION_SCHEMA_VERSION,
        finished_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=1),
        preview_payload={
            "schema_version": GENERATION_SCHEMA_VERSION,
            "prompt_version": GENERATION_PROMPT_VERSION,
            "source_context": context.provider_payload(),
            "options": options,
            "edits": {},
        },
    )


def make_option(process, owner, *, name, option_type, assessed):
    return SolutionOption.objects.create(
        process_analysis=process,
        name=name,
        option_type=option_type,
        evaluation_status=(
            SolutionOption.EvaluationStatus.ASSESSED
            if assessed
            else SolutionOption.EvaluationStatus.DRAFT
        ),
        description=f"Beschreibung {name}",
        expected_value=f"Nutzen {name}",
        bottleneck_coverage="Reduziert manuelle Übertragung.",
        feasibility=(
            SolutionOption.Effort.HIGH if assessed else SolutionOption.Effort.NOT_ASSESSED
        ),
        data_requirements="Angebote und Kriterien",
        application_impact="Ergänzung der Fachanwendung",
        integration_effort=(
            SolutionOption.Effort.MEDIUM if assessed else SolutionOption.Effort.NOT_ASSESSED
        ),
        integration_impact="ERP-Export",
        technology_constraints="Nachvollziehbare Verarbeitung",
        risks="Fehlerhafte Eingaben",
        architecture_fit="Passt zur bestehenden Architektur",
        created_by=owner,
    )


@pytest.mark.django_db
def test_preview_offers_one_adoption_choice_per_generated_option(client, owner, business_unit):
    process = make_process(owner, business_unit)
    run = make_run(owner, process)
    client.force_login(owner)

    content = client.get(
        reverse("accelerator:solution_generation_preview", args=[run.pk])
    ).content.decode()

    assert content.count('name="selected_lanes"') == 3
    for lane in OPTION_LANES:
        assert f'value="{lane}"' in content
        assert f'id="solution-adoption-{lane}"' in content
    assert content.count("Für Übernahme auswählen") == 3
    assert "Ausgewählte KI-Lösungsoptionen hinzufügen" in content
    assert 'name="selection_mode" value="explicit"' in content


@pytest.mark.django_db
def test_explicit_subset_adoption_creates_only_selected_options(client, owner, business_unit):
    process = make_process(owner, business_unit)
    run = make_run(owner, process)
    client.force_login(owner)

    response = client.post(
        reverse("accelerator:solution_generation_adopt", args=[run.pk]),
        data={
            "selection_mode": "explicit",
            "selected_lanes": ["organizational", "assistant"],
        },
    )

    assert response.status_code == 302
    options = list(SolutionOption.objects.filter(process_analysis=process))
    assert len(options) == 2
    assert {option.option_type for option in options} == {
        SolutionOption.OptionType.ORGANIZATIONAL,
        SolutionOption.OptionType.ASSISTANT,
    }
    assert all(option.recommendation == SolutionOption.Recommendation.CANDIDATE for option in options)
    assert all(option.evaluation_status == SolutionOption.EvaluationStatus.DRAFT for option in options)
    assert not SolutionSelectionDecision.objects.filter(process_analysis=process).exists()

    run.refresh_from_db()
    assert run.preview_payload["adoption"]["lanes"] == ["organizational", "assistant"]
    assert len(run.preview_payload["adoption"]["option_ids"]) == 2


@pytest.mark.django_db
def test_explicit_empty_adoption_is_rejected_without_domain_write(client, owner, business_unit):
    process = make_process(owner, business_unit)
    run = make_run(owner, process)
    client.force_login(owner)

    response = client.post(
        reverse("accelerator:solution_generation_adopt", args=[run.pk]),
        data={"selection_mode": "explicit"},
    )

    preview_url = reverse("accelerator:solution_generation_preview", args=[run.pk])
    assert response.status_code == 302
    assert response.url == f"{preview_url}#solution-generation-adoption"
    assert not SolutionOption.objects.filter(process_analysis=process).exists()
    run.refresh_from_db()
    assert "adoption" not in run.preview_payload


@pytest.mark.django_db
def test_ai_drafts_explain_why_preferred_selection_is_locked(client, owner, business_unit):
    process = make_process(owner, business_unit)
    select_focus(process, owner)
    first = make_option(
        process,
        owner,
        name="Organisatorischer Entwurf",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
        assessed=False,
    )
    second = make_option(
        process,
        owner,
        name="Assistenzentwurf",
        option_type=SolutionOption.OptionType.ASSISTANT,
        assessed=False,
    )
    client.force_login(owner)

    content = client.get(
        reverse("architecture:solution_option_compare", args=[process.pk])
    ).content.decode()

    assert "Auswahl noch gesperrt" in content
    assert "KI-Entwürfe werden absichtlich zunächst als“" not in content
    assert "KI-Entwürfe werden absichtlich zunächst als „Noch nicht bewertet“ übernommen." in content
    assert content.count("Option vollständig bewerten") == 2
    assert reverse("architecture:solution_option_update", args=[first.pk]) in content
    assert reverse("architecture:solution_option_update", args=[second.pk]) in content
    assert '<button class="btn btn-primary" type="button" disabled>Auswahl noch gesperrt</button>' in content


@pytest.mark.django_db
def test_successful_preferred_selection_returns_to_visible_local_result(
    client,
    owner,
    business_unit,
):
    process = make_process(owner, business_unit)
    select_focus(process, owner)
    organizational = make_option(
        process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
        assessed=True,
    )
    assistant = make_option(
        process,
        owner,
        name="KI-Assistenz",
        option_type=SolutionOption.OptionType.ASSISTANT,
        assessed=True,
    )
    client.force_login(owner)
    compare_url = reverse("architecture:solution_option_compare", args=[process.pk])

    response = client.post(
        compare_url,
        data={
            "selected_option": assistant.pk,
            "rationale": "Die organisatorische Alternative deckt die Extraktionsarbeit nicht ab.",
        },
    )

    assert response.status_code == 302
    assert response.url == f"{compare_url}#selection-result"
    organizational.refresh_from_db()
    assistant.refresh_from_db()
    assert organizational.recommendation == SolutionOption.Recommendation.REJECTED
    assert assistant.recommendation == SolutionOption.Recommendation.PREFERRED

    content = client.get(compare_url).content.decode()
    assert "Aktuell bevorzugt: KI-Assistenz" in content
    assert "Die Entscheidung ist in der Auswahlhistorie auditierbar." in content
    assert "Bevorzugte Option auswählen" in content
