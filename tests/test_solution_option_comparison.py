import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from ki_radar.architecture.focus import ValueStreamFocus
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
        "Mindestens zwei unterschiedliche Lösungsoptionen sind erforderlich."
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
