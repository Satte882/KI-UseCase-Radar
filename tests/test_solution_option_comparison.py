import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from ki_radar.architecture.focus import ValueStreamFocus
from ki_radar.architecture.forms import SolutionOptionForm
from ki_radar.architecture.models import (
    ProcessAnalysis,
    SolutionOption,
    SolutionSelectionDecision,
    ValueStream,
    ValueStreamStage,
)
from ki_radar.architecture.solution_selection import (
    comparison_blockers,
    ordered_solution_options,
    select_preferred_solution,
)
from ki_radar.core.taxonomy import BusinessDomain, ScreeningLevel


@pytest.fixture
def comparison_process(owner, business_unit):
    stream = ValueStream.objects.create(
        name="Beschaffung bis Zahlung",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Freigegebener Bedarf",
        outcome="Bezahlte Leistung",
        scope_in="Bedarf bis Zahlung",
        status=ValueStream.Status.ACTIVE,
    )
    ValueStreamFocus.objects.update_or_create(
        value_stream=stream,
        defaults={
            "business_domain": BusinessDomain.PROCUREMENT,
            "capability": "Source-to-Pay",
            "strategic_impact": ScreeningLevel.HIGH,
            "economic_potential": ScreeningLevel.HIGH,
            "pain_intensity": ScreeningLevel.HIGH,
            "data_accessibility": ScreeningLevel.MEDIUM,
            "change_effort": ScreeningLevel.MEDIUM,
            "status": ValueStreamFocus.Status.SELECTED,
            "rationale": "Der Value Stream ist für den Deep Dive ausgewählt.",
            "updated_by": owner,
        },
    )
    stage = ValueStreamStage.objects.create(
        value_stream=stream,
        sequence=1,
        name="Angebote vergleichen",
        description="Alternativen vergleichen.",
        actors="Einkauf",
        systems="ERP",
        documents="Angebote",
        pain_points="Manuelle Übertragung",
        baseline_metrics="Fünf Tage",
    )
    return ProcessAnalysis.objects.create(
        stage=stage,
        name="Angebotsvergleich",
        status=ProcessAnalysis.Status.TARGET_DEFINED,
        scope_start="Angebote liegen vor",
        scope_end="Lieferant ist gewählt",
        trigger="Angebotsfrist endet",
        outcome="Nachvollziehbare Auswahl",
        current_flow="Angebote manuell vergleichen.",
        roles="Einkauf und Fachbereich",
        systems="ERP und Dateiablage",
        data_objects="Angebote und Kriterien",
        bottlenecks="Manuelle Übertragung verursacht Wartezeit.",
        diagnostic_observations="Der Angebotsvergleich benötigt fünf Tage und viele Rückfragen.",
        cause_hypotheses="Uneinheitliche Formate verursachen zusätzliche Übertragungsschritte.",
        confirmed_causes=(
            "Angebotsdaten liegen nicht strukturiert vor und werden manuell übertragen."
        ),
        baseline_metrics="Fünf Tage",
        analyzed_by=owner,
    )


def make_option(process, owner, *, name, option_type, status="assessed"):
    return SolutionOption.objects.create(
        process_analysis=process,
        name=name,
        option_type=option_type,
        evaluation_status=status,
        description=f"Beschreibung {name}",
        expected_value=f"Nutzen {name}",
        bottleneck_coverage="Reduziert manuelle Übertragung.",
        feasibility=SolutionOption.Effort.HIGH,
        data_requirements="Angebote und Kriterien",
        application_impact="Ergänzung der Fachanwendung",
        integration_effort=SolutionOption.Effort.MEDIUM,
        integration_impact="ERP-Export",
        technology_constraints="Nachvollziehbare Verarbeitung",
        risks="Fehlerhafte Eingaben",
        architecture_fit="Passt zur bestehenden Architektur",
        created_by=owner,
    )


def assessed_form_data(**overrides):
    data = {
        "name": "Regelprüfung",
        "option_type": SolutionOption.OptionType.RULE_AUTOMATION,
        "evaluation_status": SolutionOption.EvaluationStatus.ASSESSED,
        "description": "Beschreibung Regelprüfung",
        "expected_value": "Nutzen Regelprüfung",
        "bottleneck_coverage": "Reduziert manuelle Übertragung.",
        "feasibility": SolutionOption.Effort.HIGH,
        "data_requirements": "Angebote und Kriterien",
        "application_impact": "Ergänzung der Fachanwendung",
        "integration_effort": SolutionOption.Effort.MEDIUM,
        "integration_impact": "ERP-Export",
        "technology_constraints": "Nachvollziehbare Verarbeitung",
        "risks": "Fehlerhafte Eingaben",
        "architecture_fit": "Passt zur bestehenden Architektur",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_new_solution_option_defaults_are_not_assessed(comparison_process, owner):
    option = SolutionOption.objects.create(
        process_analysis=comparison_process,
        name="Neuer Entwurf",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
        description="Beschreibung",
        expected_value="Erwarteter Beitrag",
        created_by=owner,
    )

    assert option.feasibility == SolutionOption.Effort.NOT_ASSESSED
    assert option.integration_effort == SolutionOption.Effort.NOT_ASSESSED
    assert option.get_feasibility_display() == "Noch nicht bewertet"
    assert option.get_integration_effort_display() == "Noch nicht bewertet"
    assert option.comparison_complete is False


@pytest.mark.django_db
def test_explicit_existing_assessments_remain_unchanged(comparison_process, owner):
    option = make_option(
        comparison_process,
        owner,
        name="Bestehende Bewertung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
    )
    option.refresh_from_db()

    assert option.feasibility == SolutionOption.Effort.HIGH
    assert option.integration_effort == SolutionOption.Effort.MEDIUM
    assert option.comparison_complete is True


@pytest.mark.django_db
@pytest.mark.parametrize("field_name", ["feasibility", "integration_effort"])
def test_assessed_form_rejects_unassessed_effort(comparison_process, field_name):
    form = SolutionOptionForm(
        data=assessed_form_data(**{field_name: SolutionOption.Effort.NOT_ASSESSED}),
        process_analysis=comparison_process,
    )

    assert not form.is_valid()
    assert field_name in form.errors
    assert "muss für den Status 'Bewertet' bewertet sein" in form.errors[field_name][0]


@pytest.mark.django_db
def test_comparison_complete_rejects_unassessed_effort(comparison_process, owner):
    option = make_option(
        comparison_process,
        owner,
        name="Unvollständige Bewertung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
    )
    option.feasibility = SolutionOption.Effort.NOT_ASSESSED

    assert option.comparison_complete is False


@pytest.mark.django_db
def test_options_are_sorted_solution_open(comparison_process, owner):
    ai = make_option(
        comparison_process,
        owner,
        name="KI-Assistenz",
        option_type=SolutionOption.OptionType.ASSISTANT,
    )
    rule = make_option(
        comparison_process,
        owner,
        name="Regelprüfung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
    )
    organizational = make_option(
        comparison_process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
    )

    assert ordered_solution_options(comparison_process) == [organizational, rule, ai]


@pytest.mark.django_db
def test_comparison_requires_two_complete_options(comparison_process, owner):
    first = make_option(
        comparison_process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
    )
    assert comparison_blockers([first]) == [
        "Für die spätere Auswahl sind mindestens zwei unterschiedliche, gespeicherte "
        "Lösungsoptionen erforderlich."
    ]

    second = make_option(
        comparison_process,
        owner,
        name="Regelprüfung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
        status=SolutionOption.EvaluationStatus.DRAFT,
    )
    blockers = comparison_blockers([first, second])
    assert "Regelprüfung" in blockers[0]


@pytest.mark.django_db
def test_selection_is_auditable_and_updates_statuses(comparison_process, owner):
    organizational = make_option(
        comparison_process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
    )
    assistant = make_option(
        comparison_process,
        owner,
        name="KI-Assistenz",
        option_type=SolutionOption.OptionType.ASSISTANT,
    )

    decision = select_preferred_solution(
        process_analysis=comparison_process,
        selected_option=assistant,
        rationale="Die organisatorische Option reduziert nicht die verbleibende Extraktionsarbeit.",
        actor=owner,
    )

    organizational.refresh_from_db()
    assistant.refresh_from_db()
    assert organizational.recommendation == SolutionOption.Recommendation.REJECTED
    assert assistant.recommendation == SolutionOption.Recommendation.PREFERRED
    assert decision.decided_by == owner
    assert decision.comparison_snapshot[0]["name"] == organizational.name
    assert len(decision.comparison_snapshot) == 2

    decision.rationale = "Nachträglich geändert"
    with pytest.raises(ValidationError):
        decision.save()
    with pytest.raises(ValidationError):
        decision.delete()


@pytest.mark.django_db
def test_selection_rejects_unauthorized_reader(comparison_process, owner, reader):
    first = make_option(
        comparison_process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
    )
    make_option(
        comparison_process,
        owner,
        name="Regelprüfung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
    )

    with pytest.raises(ValidationError, match="Berechtigung"):
        select_preferred_solution(
            process_analysis=comparison_process,
            selected_option=first,
            rationale="Nicht berechtigt.",
            actor=reader,
        )


@pytest.mark.django_db
def test_comparison_page_selects_and_shows_history(client, comparison_process, owner):
    organizational = make_option(
        comparison_process,
        owner,
        name="Vorlage standardisieren",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
    )
    assistant = make_option(
        comparison_process,
        owner,
        name="KI-Assistenz",
        option_type=SolutionOption.OptionType.ASSISTANT,
    )
    client.force_login(owner)
    url = reverse("architecture:solution_option_compare", kwargs={"pk": comparison_process.pk})

    response = client.get(url)
    content = response.content.decode()
    assert response.status_code == 200
    assert "Vergleichsmatrix" in content
    assert content.index(organizational.name) < content.index(assistant.name)
    assert "Bottleneck-Abdeckung" in content
    assert "Integrationsaufwand" in content
    assert "Technologieleitplanken" in content

    response = client.post(
        url,
        {
            "selected_option": assistant.pk,
            "rationale": "Die organisatorische Alternative deckt die Extraktionsarbeit nicht ab.",
        },
    )
    assert response.status_code == 302
    decision = SolutionSelectionDecision.objects.get(process_analysis=comparison_process)
    assert decision.selected_option == assistant

    history = client.get(url).content.decode()
    assert "Auswahlhistorie" in history
    assert "Die organisatorische Alternative" in history


@pytest.mark.django_db
def test_comparison_page_handles_unassessed_and_empty_technology_constraints(
    client,
    comparison_process,
    owner,
):
    option = SolutionOption.objects.create(
        process_analysis=comparison_process,
        name="Ältere manuelle Option",
        option_type=SolutionOption.OptionType.ORGANIZATIONAL,
        description="Beschreibung",
        expected_value="Nutzen",
        feasibility=SolutionOption.Effort.MEDIUM,
        integration_effort=SolutionOption.Effort.MEDIUM,
        technology_constraints="",
        created_by=owner,
    )
    new_option = SolutionOption.objects.create(
        process_analysis=comparison_process,
        name="Neutraler Entwurf",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
        description="Beschreibung",
        expected_value="Nutzen",
        created_by=owner,
    )
    client.force_login(owner)
    url = reverse("architecture:solution_option_compare", kwargs={"pk": comparison_process.pk})

    content = client.get(url).content.decode()

    assert option.name in content
    assert new_option.name in content
    assert "Noch nicht bewertet" in content
    assert "Technologieleitplanken" in content
    assert "\u2013" in content


@pytest.mark.django_db
def test_selection_audit_rejects_bulk_changes_and_inconsistent_option(
    comparison_process,
    owner,
    business_unit,
):
    from django.db.models.deletion import ProtectedError

    selected = make_option(
        comparison_process,
        owner,
        name="Regelprüfung",
        option_type=SolutionOption.OptionType.RULE_AUTOMATION,
    )
    alternative = make_option(
        comparison_process,
        owner,
        name="KI-Assistenz",
        option_type=SolutionOption.OptionType.ASSISTANT,
    )
    decision = select_preferred_solution(
        process_analysis=comparison_process,
        selected_option=selected,
        rationale="Die Regelprüfung deckt den Engpass mit geringerer Komplexität ab.",
        actor=owner,
    )

    with pytest.raises(ValidationError, match="unveränderlich"):
        SolutionSelectionDecision.objects.filter(pk=decision.pk).update(rationale="Manipuliert")
    with pytest.raises(ValidationError, match="unveränderlich"):
        SolutionSelectionDecision.objects.filter(pk=decision.pk).delete()
    with pytest.raises(ProtectedError):
        selected.delete()

    other_stream = ValueStream.objects.create(
        name="Anderer Wertstrom",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Start",
        outcome="Ergebnis",
        scope_in="Scope",
    )
    other_stage = ValueStreamStage.objects.create(
        value_stream=other_stream,
        sequence=1,
        name="Andere Phase",
    )
    other_process = ProcessAnalysis.objects.create(
        stage=other_stage,
        name="Anderer Prozess",
        scope_start="Start",
        scope_end="Ende",
        trigger="Start",
        outcome="Ergebnis",
        current_flow="Ablauf",
        roles="Rolle",
        systems="System",
        data_objects="Daten",
        bottlenecks="Engpass",
        baseline_metrics="Baseline",
        analyzed_by=owner,
    )
    with pytest.raises(ValidationError, match="gehört nicht"):
        SolutionSelectionDecision.objects.create(
            process_analysis=other_process,
            selected_option=alternative,
            rationale="Inkonsistente Zuordnung",
            comparison_snapshot=[],
            decided_by=owner,
        )
