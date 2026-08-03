from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:160]!r}")
    file_path.write_text(text.replace(old, new, count), encoding="utf-8")


# Canonical fields: preserve existing data by renaming scope to scope_in.
replace(
    "ki_radar/architecture/models.py",
    '    scope = models.TextField(verbose_name="Scope und Abgrenzung")\n',
    '    scope_in = models.TextField(verbose_name="Im Scope")\n'
    '    scope_out = models.TextField(blank=True, verbose_name="Nicht im Scope")\n',
)

replace(
    "ki_radar/architecture/forms.py",
    '            "scope",\n',
    '            "scope_in",\n            "scope_out",\n',
)
replace(
    "ki_radar/architecture/forms.py",
    '            "scope": forms.Textarea(attrs={"rows": 3}),\n',
    '            "scope_in": forms.Textarea(attrs={"rows": 3}),\n'
    '            "scope_out": forms.Textarea(attrs={"rows": 3}),\n',
)
replace(
    "ki_radar/architecture/forms.py",
    '        self.fields["owner"].queryset = owners\n',
    '        self.fields["scope_in"].help_text = (\n'
    '            "Verbindlicher Umfang dieses Value Streams."\n'
    '        )\n'
    '        self.fields["scope_out"].help_text = (\n'
    '            "Optional, aber empfohlen: ausdrücklich ausgeschlossene Bereiche."\n'
    '        )\n'
    '        self.fields["owner"].queryset = owners\n',
)

replace(
    "templates/architecture/value_stream_detail.html",
    '  <section class="app-card card-body"><div class="section-title">Scope</div><p class="mb-0">{{ value_stream.scope }}</p></section>\n',
    '  <section class="app-card card-body"><div class="section-title">Im Scope</div><p class="mb-0">{{ value_stream.scope_in }}</p></section>\n'
    '  <section class="app-card card-body"><div class="section-title">Nicht im Scope</div><p class="mb-0">{{ value_stream.scope_out|default:"Nicht ausdrücklich abgegrenzt" }}</p></section>\n',
)
replace(
    "templates/architecture/value_stream_list.html",
    "{{ stream.description|default:stream.scope|truncatechars:180 }}",
    "{{ stream.description|default:stream.scope_in|truncatechars:180 }}",
)

replace(
    "templates/architecture/process_analysis_form.html",
    '<form method="post" class="app-card">\n',
    '<div class="app-card mb-4">\n'
    '  <div class="card-header"><strong>Quellkontext aus dem Value Stream</strong><div class="small text-muted mt-1">Referenziert, nicht in Prozessfelder kopiert. Änderungen bleiben am führenden Value Stream sichtbar.</div></div>\n'
    '  <div class="card-body"><div class="row g-4">\n'
    '    <div class="col-md-6"><div class="section-title">Im Scope</div><div class="text-preline">{{ stage.value_stream.scope_in }}</div></div>\n'
    '    <div class="col-md-6"><div class="section-title">Nicht im Scope</div><div class="text-preline">{{ stage.value_stream.scope_out|default:"Nicht ausdrücklich abgegrenzt" }}</div></div>\n'
    '  </div></div>\n'
    '</div>\n\n'
    '<form method="post" class="app-card">\n',
)

# Demo and golden-path data use the separated fields.
for path in [
    "ki_radar/core/golden_path_demo.py",
    "ki_radar/core/demo_architecture_data.py",
]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    text = text.replace('"scope": ', '"scope_in": ')
    file_path.write_text(text, encoding="utf-8")

# Give the demo scenarios concrete exclusions where they matter.
replace(
    "ki_radar/core/golden_path_demo.py",
    '            "scope_in": "Bedarf, Lieferantenauswahl, Bestellung, Lieferung, Leistung und Zahlung.",\n',
    '            "scope_in": "Bedarf, Lieferantenauswahl, Bestellung, Lieferung, Leistung und Zahlung.",\n'
    '            "scope_out": "Vertragsverhandlung und autonome Vergabeentscheidung.",\n',
)
replace(
    "ki_radar/core/demo_architecture_data.py",
    '            "scope_in": "Bedarf, Beschaffung, Leistungserbringung und Zahlung.",\n',
    '            "scope_in": "Bedarf, Beschaffung, Leistungserbringung und Zahlung.",\n'
    '            "scope_out": "Strategische Lieferantenentwicklung und Vertragsverhandlung.",\n',
)
replace(
    "ki_radar/core/demo_architecture_data.py",
    '            "scope_in": "Lieferantensuche, Anfrage, Angebotsvergleich und Auswahlentscheidung.",\n',
    '            "scope_in": "Lieferantensuche, Anfrage, Angebotsvergleich und Auswahlentscheidung.",\n'
    '            "scope_out": "Vertragsabschluss und operative Leistungserbringung.",\n',
)
replace(
    "ki_radar/core/demo_architecture_data.py",
    '            "scope_in": "Bedarfsmeldung, Prüfung, Freigabe und Bestellung.",\n',
    '            "scope_in": "Bedarfsmeldung, Prüfung, Freigabe und Bestellung.",\n'
    '            "scope_out": "Wareneingang, Rechnungsprüfung und Zahlung.",\n',
)

# Update existing tests and request payloads without maintaining a legacy alias.
for path in [
    "tests/test_process_analysis.py",
    "tests/test_issue_58_value_stream_next_action.py",
    "tests/test_value_stream_assignments.py",
    "tests/test_delivery_handover.py",
    "tests/test_focus_prioritization.py",
    "tests/test_architecture_discovery.py",
    "tests/test_issue_58_solution_next_action.py",
]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    text = text.replace("scope=", "scope_in=")
    text = text.replace('"scope":', '"scope_in":')
    file_path.write_text(text, encoding="utf-8")

Path("ki_radar/architecture/migrations/0006_split_value_stream_scope.py").write_text(
    '''from django.db import migrations, models\n\n\nclass Migration(migrations.Migration):\n    dependencies = [\n        ("architecture", "0005_backfill_value_stream_focus"),\n    ]\n\n    operations = [\n        migrations.RenameField(\n            model_name="valuestream",\n            old_name="scope",\n            new_name="scope_in",\n        ),\n        migrations.AlterField(\n            model_name="valuestream",\n            name="scope_in",\n            field=models.TextField(verbose_name="Im Scope"),\n        ),\n        migrations.AddField(\n            model_name="valuestream",\n            name="scope_out",\n            field=models.TextField(blank=True, verbose_name="Nicht im Scope"),\n        ),\n    ]\n''',
    encoding="utf-8",
)

Path("tests/test_value_stream_scope.py").write_text(
    '''import pytest\nfrom django.urls import reverse\n\nfrom ki_radar.architecture.forms import ValueStreamForm\nfrom ki_radar.architecture.models import ValueStream, ValueStreamStage\n\n\ndef form_data(business_unit, owner, **overrides):\n    data = {\n        "name": "Anfrage bis Abschluss",\n        "business_unit": business_unit.pk,\n        "owner": owner.pk,\n        "status": ValueStream.Status.DRAFT,\n        "description": "Kundenanfragen bearbeiten.",\n        "trigger": "Anfrage geht ein",\n        "outcome": "Anfrage ist abgeschlossen",\n        "scope_in": "Annahme, Bearbeitung und Abschluss der Anfrage",\n        "scope_out": "Vertragsänderungen und Abrechnung",\n        "strategic_objective": "Durchlaufzeit reduzieren",\n        "stakeholders": "Kundenservice",\n        "constraints": "Bestehendes CRM",\n        "business_domain": "other",\n        "capability": "",\n        "strategic_impact": "",\n        "economic_potential": "",\n        "pain_intensity": "",\n        "data_accessibility": "",\n        "change_effort": "",\n        "focus_status": "not_screened",\n        "focus_rationale": "",\n    }\n    data.update(overrides)\n    return data\n\n\n@pytest.mark.django_db\ndef test_scope_in_is_required_and_scope_out_is_optional(business_unit, owner):\n    missing_scope = ValueStreamForm(\n        data=form_data(business_unit, owner, scope_in="", scope_out="")\n    )\n    optional_exclusion = ValueStreamForm(\n        data=form_data(business_unit, owner, scope_out="")\n    )\n\n    assert missing_scope.is_valid() is False\n    assert "scope_in" in missing_scope.errors\n    assert optional_exclusion.is_valid(), optional_exclusion.errors\n\n\n@pytest.mark.django_db\ndef test_value_stream_detail_displays_scope_and_exclusion_separately(\n    client, business_unit, owner\n):\n    value_stream = ValueStream.objects.create(\n        name="Getrennter Scope",\n        business_unit=business_unit,\n        owner=owner,\n        trigger="Start",\n        outcome="Ergebnis",\n        scope_in="Anfrage bis Entscheidung",\n        scope_out="Vertragsabschluss",\n    )\n    client.force_login(owner)\n\n    response = client.get(value_stream.get_absolute_url())\n\n    content = response.content.decode()\n    assert response.status_code == 200\n    assert "Im Scope" in content\n    assert "Anfrage bis Entscheidung" in content\n    assert "Nicht im Scope" in content\n    assert "Vertragsabschluss" in content\n\n\n@pytest.mark.django_db\ndef test_process_analysis_references_value_stream_scope_without_copying(\n    client, business_unit, owner\n):\n    value_stream = ValueStream.objects.create(\n        name="Referenzierter Scope",\n        business_unit=business_unit,\n        owner=owner,\n        trigger="Start",\n        outcome="Ergebnis",\n        scope_in="Prüfung und Entscheidung",\n        scope_out="Operative Ausführung",\n    )\n    stage = ValueStreamStage.objects.create(\n        value_stream=value_stream, sequence=1, name="Prüfen"\n    )\n    client.force_login(owner)\n\n    response = client.get(reverse("architecture:process_analysis_create", args=[stage.pk]))\n\n    content = response.content.decode()\n    assert response.status_code == 302  # Fokusentscheidung ist weiterhin das vorgelagerte Gate.\n    assert not hasattr(stage, "scope_in")\n    assert stage.value_stream.scope_in == "Prüfung und Entscheidung"\n    assert stage.value_stream.scope_out == "Operative Ausführung"\n''',
    encoding="utf-8",
)
