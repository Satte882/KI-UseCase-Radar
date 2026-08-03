# ruff: noqa: F403,F405
from _delivery_handover_cases import *


@pytest.mark.django_db
def test_delivery_package_uses_optional_architecture_origin(
    owner,
    coordinator,
    business_unit,
):
    use_case = make_use_case(owner, business_unit)
    approve_use_case(use_case, coordinator)
    stream = ValueStream.objects.create(
        name="Beschaffung bis Zahlung",
        business_unit=business_unit,
        owner=owner,
        created_by=owner,
        trigger="Freigegebener Bedarf",
        outcome="Bezahlte Leistung",
        scope_in="Bedarf bis Zahlung",
        constraints="ERP bleibt führendes System.",
    )
    stage = ValueStreamStage.objects.create(
        value_stream=stream,
        sequence=1,
        name="Lieferantenauswahl",
        description="Angebote vergleichen und Entscheidung vorbereiten.",
        actors="Einkauf und Fachbereich",
        systems="ERP und Dateiablage",
        documents="Angebote und Kriterienkatalog",
        pain_points="Manuelle Übertragung",
        baseline_metrics="Fünf Tage",
    )
    process = ProcessAnalysis.objects.create(
        stage=stage,
        name="Angebotsvergleich",
        scope_start="Angebote liegen vor",
        scope_end="Lieferant ist ausgewählt",
        trigger="Angebotsfrist endet",
        outcome="Nachvollziehbare Entscheidung",
        current_flow="Angebote öffnen, Daten übertragen und bewerten.",
        roles="Einkauf und Fachbereich",
        systems="ERP, Shared Inbox, Dateiablage",
        data_objects="Angebote und Kriterien",
        bottlenecks="Manuelle Übertragung und Rückfragen",
        baseline_metrics="Fünf Tage",
        handoffs="Einkauf übergibt Shortlist an Fachbereich.",
        exceptions="Fehlende Preise und Einheiten.",
        analyzed_by=owner,
    )
    option = SolutionOption.objects.create(
        process_analysis=process,
        name="Assistierter Vergleich",
        option_type=SolutionOption.OptionType.ASSISTANT,
        recommendation=SolutionOption.Recommendation.PREFERRED,
        description="Extraktion und Vergleich mit menschlicher Freigabe.",
        expected_value="Durchlaufzeit reduzieren",
        data_requirements="Angebote und Kriterien",
        integration_impact="Dateiablage und ERP-Export",
        risks="Ungewöhnliche Tabellen",
        architecture_fit="Passt zur bestehenden Systemlandschaft.",
        created_by=owner,
    )
    UseCaseOrigin.objects.create(
        use_case=use_case,
        stage=stage,
        process_analysis=process,
        solution_option=option,
    )

    package = create_delivery_package(use_case=use_case, actor=coordinator)

    assert package.in_scope == stream.scope_in
    scope_manifest = package.section_reviews.get(
        section_key="scope_and_users"
    ).source_manifest
    assert (
        scope_manifest["fields"]["in_scope"]["artifact_label"] == "Value Stream"
    )
    assert (
        scope_manifest["fields"]["in_scope"]["source_value"] == stream.scope_in
    )
    assert package.solution_outline == option.description
    assert package.system_context == process.systems
    assert package.integrations == option.integration_impact
    assert package.architecture_decisions == option.architecture_fit
    assert process.exceptions in package.test_scenarios
    assert process.exceptions not in package.assumptions
