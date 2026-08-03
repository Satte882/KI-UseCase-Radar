from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:180]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Model: explicit process version plus immutable validation records.
replace(
    "ki_radar/architecture/models.py",
    "from django.urls import reverse\n",
    "from django.urls import reverse\nfrom django.utils import timezone\n",
)
replace(
    "ki_radar/architecture/models.py",
    '''    class Status(models.TextChoices):\n        DRAFT = "draft", "Entwurf"\n        VALIDATED = "validated", "Ist-Prozess validiert"\n        TARGET_DEFINED = "target_defined", "Zielbild beschrieben"\n''',
    '''    class Status(models.TextChoices):\n        DRAFT = "draft", "Entwurf"\n        REVIEW_REQUIRED = "review_required", "Prüfbedürftig"\n        VALIDATED = "validated", "Ist-Prozess validiert"\n        TARGET_DEFINED = "target_defined", "Zielbild beschrieben"\n''',
)
replace(
    "ki_radar/architecture/models.py",
    '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n',
    '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n'
    '    version = models.PositiveIntegerField(default=1, editable=False)\n',
)
replace(
    "ki_radar/architecture/models.py",
    '''    def get_absolute_url(self):\n        return reverse("architecture:process_analysis_detail", kwargs={"pk": self.pk})\n\n\nclass SolutionOption(TimeStampedModel):\n''',
    '''    def get_absolute_url(self):\n        return reverse("architecture:process_analysis_detail", kwargs={"pk": self.pk})\n\n\nclass ProcessValidation(TimeStampedModel):\n    process_analysis = models.ForeignKey(\n        ProcessAnalysis,\n        on_delete=models.CASCADE,\n        related_name="validations",\n    )\n    process_version = models.PositiveIntegerField()\n    validated_by = models.ForeignKey(\n        settings.AUTH_USER_MODEL,\n        null=True,\n        on_delete=models.SET_NULL,\n        related_name="process_validations",\n    )\n    validator_role = models.CharField(max_length=100)\n    validated_at = models.DateTimeField(default=timezone.now, editable=False)\n    note = models.TextField(blank=True, verbose_name="Validierungsnotiz")\n    evidence_url = models.URLField(blank=True, verbose_name="Nachweis")\n\n    class Meta:\n        ordering = ["-validated_at"]\n        constraints = [\n            models.UniqueConstraint(\n                fields=["process_analysis", "process_version"],\n                name="unique_process_validation_version",\n            )\n        ]\n\n    def __str__(self) -> str:\n        return f"{self.process_analysis.name} · Validierung v{self.process_version}"\n\n\nclass SolutionOption(TimeStampedModel):\n''',
)

# Form: status remains available for workflow states, but validation cannot be self-declared.
replace(
    "ki_radar/architecture/forms.py",
    '''class ProcessAnalysisForm(StyledModelForm):\n    class Meta:\n''',
    '''class ProcessAnalysisForm(StyledModelForm):\n    def clean_status(self):\n        status = self.cleaned_data["status"]\n        if status == ProcessAnalysis.Status.VALIDATED and (\n            not self.instance.pk or self.instance.status != ProcessAnalysis.Status.VALIDATED\n        ):\n            raise forms.ValidationError(\n                "Der Status 'Ist-Prozess validiert' wird ausschließlich über die "\n                "eigenständige Validierungsaktion gesetzt."\n            )\n        return status\n\n    class Meta:\n''',
)
replace(
    "ki_radar/architecture/forms.py",
    '''\n\nclass SolutionOptionForm(StyledModelForm):\n''',
    '''\n\nclass ProcessValidationForm(forms.Form):\n    note = forms.CharField(\n        required=False,\n        label="Validierungsnotiz",\n        widget=forms.Textarea(attrs={"rows": 4, "class": FORM_CONTROL}),\n        help_text="Optional: geprüfte Grundlage, Einschränkungen oder Hinweise.",\n    )\n    evidence_url = forms.URLField(\n        required=False,\n        label="Nachweis",\n        widget=forms.URLInput(attrs={"class": FORM_CONTROL}),\n        help_text="Optionaler Link auf Protokoll, Workshop-Ergebnis oder andere Evidenz.",\n    )\n\n\nclass SolutionOptionForm(StyledModelForm):\n''',
)

# View imports and helpers.
replace(
    "ki_radar/architecture/views.py",
    "from django.shortcuts import get_object_or_404, redirect, render\n",
    "from django.shortcuts import get_object_or_404, redirect, render\n",
)
replace(
    "ki_radar/architecture/views.py",
    "from ki_radar.use_cases.intake_views import SESSION_KEY\n",
    "from ki_radar.accounts.permissions import (\n"
    "    GROUP_COORDINATOR,\n"
    "    in_group,\n"
    "    is_technical_admin,\n"
    ")\n"
    "from ki_radar.use_cases.intake_views import SESSION_KEY\n",
)
replace(
    "ki_radar/architecture/views.py",
    '''    ProcessAnalysisForm,\n    SolutionOptionForm,\n''',
    '''    ProcessAnalysisForm,\n    ProcessValidationForm,\n    SolutionOptionForm,\n''',
)
replace(
    "ki_radar/architecture/views.py",
    "from .models import ProcessAnalysis, SolutionOption, ValueStream, ValueStreamStage\n",
    "from .models import (\n"
    "    ProcessAnalysis,\n"
    "    ProcessValidation,\n"
    "    SolutionOption,\n"
    "    ValueStream,\n"
    "    ValueStreamStage,\n"
    ")\n",
)
replace(
    "ki_radar/architecture/views.py",
    '''FOCUS_REQUIRED_MESSAGE = (\n    "Der Value Stream muss zuerst vollständig bewertet und für einen Deep Dive ausgewählt werden."\n)\n\n\ndef _can_edit_process''',
    '''FOCUS_REQUIRED_MESSAGE = (\n    "Der Value Stream muss zuerst vollständig bewertet und für einen Deep Dive ausgewählt werden."\n)\nPROCESS_VALIDATION_FIELDS = {\n    "name",\n    "scope_start",\n    "scope_end",\n    "trigger",\n    "outcome",\n    "current_flow",\n    "roles",\n    "systems",\n    "data_objects",\n    "business_rules",\n    "handoffs",\n    "bottlenecks",\n    "exceptions",\n    "baseline_metrics",\n}\n\n\ndef _validator_role(user) -> str:\n    if is_technical_admin(user):\n        return "Technischer Administrator"\n    if in_group(user, GROUP_COORDINATOR):\n        return "KI-Koordinator"\n    return "Business Owner"\n\n\ndef _can_edit_process''',
)

# Detail loads and exposes the immutable history.
replace(
    "ki_radar/architecture/views.py",
    '''            "analyzed_by",\n        ).prefetch_related(\n            "solution_options",\n''',
    '''            "analyzed_by",\n        ).prefetch_related(\n            "validations__validated_by",\n            "solution_options",\n''',
)
replace(
    "ki_radar/architecture/views.py",
    '''            "can_edit": _can_edit_process(request.user, process_analysis),\n            "can_create_use_case": can_create_use_case(request.user),\n''',
    '''            "can_edit": _can_edit_process(request.user, process_analysis),\n            "can_validate": _can_edit_process(request.user, process_analysis),\n            "latest_validation": process_analysis.validations.first(),\n            "can_create_use_case": can_create_use_case(request.user),\n''',
)

# Essential edits create a new process version and invalidate only a prior validation.
replace(
    "ki_radar/architecture/views.py",
    '''    if request.method == "POST" and form.is_valid():\n        form.save()\n        messages.success(request, "Prozessanalyse wurde aktualisiert.")\n        return redirect(process_analysis)\n''',
    '''    if request.method == "POST" and form.is_valid():\n        validation_relevant_change = bool(\n            set(form.changed_data).intersection(PROCESS_VALIDATION_FIELDS)\n        )\n        had_validation = process_analysis.validations.filter(\n            process_version=process_analysis.version\n        ).exists()\n        updated_process = form.save(commit=False)\n        if validation_relevant_change:\n            updated_process.version += 1\n            if had_validation or process_analysis.status == ProcessAnalysis.Status.VALIDATED:\n                updated_process.status = ProcessAnalysis.Status.REVIEW_REQUIRED\n        updated_process.save()\n        if validation_relevant_change and updated_process.status == ProcessAnalysis.Status.REVIEW_REQUIRED:\n            messages.warning(\n                request,\n                "Wesentliche Prozessinformationen wurden geändert. "\n                "Die aktuelle Version muss erneut validiert werden.",\n            )\n        else:\n            messages.success(request, "Prozessanalyse wurde aktualisiert.")\n        return redirect(updated_process)\n''',
)

# Dedicated validation action.
replace(
    "ki_radar/architecture/views.py",
    '''\n\n@login_required\ndef solution_option_create(request, process_analysis_id):\n''',
    '''\n\n@login_required\ndef process_analysis_validate(request, pk):\n    process_analysis = get_object_or_404(\n        ProcessAnalysis.objects.select_related("stage__value_stream"),\n        pk=pk,\n    )\n    if not _can_edit_process(request.user, process_analysis):\n        raise PermissionDenied\n    existing = process_analysis.validations.filter(\n        process_version=process_analysis.version\n    ).first()\n    if existing is not None:\n        messages.info(request, "Diese Prozessversion ist bereits nachvollziehbar validiert.")\n        return redirect(process_analysis)\n    form = ProcessValidationForm(request.POST or None)\n    if request.method == "POST" and form.is_valid():\n        ProcessValidation.objects.create(\n            process_analysis=process_analysis,\n            process_version=process_analysis.version,\n            validated_by=request.user,\n            validator_role=_validator_role(request.user),\n            note=form.cleaned_data["note"],\n            evidence_url=form.cleaned_data["evidence_url"],\n        )\n        process_analysis.status = ProcessAnalysis.Status.VALIDATED\n        process_analysis.save(update_fields=["status", "updated_at"])\n        messages.success(request, "Die aktuelle Prozessversion wurde validiert.")\n        return redirect(process_analysis)\n    return render(\n        request,\n        "architecture/process_validation_form.html",\n        {"form": form, "process_analysis": process_analysis},\n    )\n\n\n@login_required\ndef solution_option_create(request, process_analysis_id):\n''',
)

# Route.
replace(
    "ki_radar/architecture/urls.py",
    '''    path(\n        "processes/<uuid:pk>/edit/",\n        views.process_analysis_update,\n        name="process_analysis_update",\n    ),\n''',
    '''    path(\n        "processes/<uuid:pk>/edit/",\n        views.process_analysis_update,\n        name="process_analysis_update",\n    ),\n    path(\n        "processes/<uuid:pk>/validate/",\n        views.process_analysis_validate,\n        name="process_analysis_validate",\n    ),\n''',
)

# Detail card and action.
replace(
    "templates/architecture/process_analysis_detail.html",
    '''    {% if can_edit %}<a class="btn btn-primary" href="{% url 'architecture:process_analysis_update' process_analysis.pk %}">Bearbeiten</a>{% endif %}\n''',
    '''    {% if can_validate and process_analysis.status != 'validated' %}<a class="btn btn-outline-primary" href="{% url 'architecture:process_analysis_validate' process_analysis.pk %}">Ist-Prozess validieren</a>{% endif %}\n    {% if can_edit %}<a class="btn btn-primary" href="{% url 'architecture:process_analysis_update' process_analysis.pk %}">Bearbeiten</a>{% endif %}\n''',
)
replace(
    "templates/architecture/process_analysis_detail.html",
    '''{% if not process_analysis.stage.value_stream.focus.is_selected %}<div class="alert alert-warning"><strong>Deep Dive nicht freigegeben:</strong> Der übergeordnete Value Stream muss zuerst vollständig bewertet und für die Vertiefung ausgewählt werden.</div>{% endif %}\n\n<div class="architecture-summary-grid mb-4">\n''',
    '''{% if not process_analysis.stage.value_stream.focus.is_selected %}<div class="alert alert-warning"><strong>Deep Dive nicht freigegeben:</strong> Der übergeordnete Value Stream muss zuerst vollständig bewertet und für die Vertiefung ausgewählt werden.</div>{% endif %}\n\n<div class="app-card mb-4" id="process-validation">\n  <div class="card-header d-flex flex-wrap justify-content-between align-items-start gap-3">\n    <div><strong>Validierung des Ist-Prozesses</strong><div class="small text-muted mt-1">Eigenständiger Nachweis für die konkret geprüfte Prozessversion.</div></div>\n    <span class="badge {% if process_analysis.status == 'validated' %}state-ready{% elif process_analysis.status == 'review_required' %}state-blocked{% else %}state-review{% endif %}">{{ process_analysis.get_status_display }}</span>\n  </div>\n  <div class="card-body">\n    <div class="small text-muted mb-3">Aktuelle Prozessversion: <strong>v{{ process_analysis.version }}</strong></div>\n    {% if latest_validation and latest_validation.process_version == process_analysis.version %}\n    <dl class="row mb-0">\n      <dt class="col-sm-4 text-muted">Geprüfte Version</dt><dd class="col-sm-8">v{{ latest_validation.process_version }}</dd>\n      <dt class="col-sm-4 text-muted">Validiert durch</dt><dd class="col-sm-8">{{ latest_validation.validated_by.get_display_name|default:"Nicht mehr verfügbar" }}</dd>\n      <dt class="col-sm-4 text-muted">Rolle</dt><dd class="col-sm-8">{{ latest_validation.validator_role }}</dd>\n      <dt class="col-sm-4 text-muted">Zeitpunkt</dt><dd class="col-sm-8">{{ latest_validation.validated_at|date:"d.m.Y H:i" }}</dd>\n      <dt class="col-sm-4 text-muted">Notiz</dt><dd class="col-sm-8 text-preline">{{ latest_validation.note|default:"Keine zusätzliche Notiz" }}</dd>\n      <dt class="col-sm-4 text-muted">Nachweis</dt><dd class="col-sm-8">{% if latest_validation.evidence_url %}<a href="{{ latest_validation.evidence_url }}" target="_blank" rel="noopener noreferrer">Validierungsnachweis öffnen</a>{% else %}Kein separater Nachweis hinterlegt{% endif %}</dd>\n    </dl>\n    {% else %}\n    <div class="alert alert-warning mb-0"><strong>Keine Validierung für Version v{{ process_analysis.version }}.</strong> Der angezeigte Prozessstatus ist noch nicht durch ein eigenständiges Validierungsartefakt belegt.</div>\n    {% endif %}\n    {% if process_analysis.validations.all %}\n    <hr>\n    <div class="section-title">Historische Validierungen</div>\n    <ul class="mb-0">{% for validation in process_analysis.validations.all %}<li>v{{ validation.process_version }} · {{ validation.validated_at|date:"d.m.Y H:i" }} · {{ validation.validator_role }} · {% if validation.validated_by %}{{ validation.validated_by.get_display_name }}{% else %}Person nicht mehr verfügbar{% endif %}</li>{% endfor %}</ul>\n    {% endif %}\n  </div>\n</div>\n\n<div class="architecture-summary-grid mb-4">\n''',
)

Path("templates/architecture/process_validation_form.html").write_text(
    '''{% extends "base.html" %}\n{% block title %}Ist-Prozess validieren – KI-Radar{% endblock %}\n{% block content %}\n<div class="page-header">\n  <div><div class="eyebrow mb-2">{{ process_analysis.stage.value_stream.name }} · {{ process_analysis.stage.name }}</div><h1 class="page-title">Ist-Prozess validieren</h1><p class="page-subtitle">Geprüft wird ausschließlich die aktuelle Prozessversion v{{ process_analysis.version }}. Notiz und Nachweis sind optional.</p></div>\n  <a class="btn btn-outline-secondary" href="{{ process_analysis.get_absolute_url }}">Abbrechen</a>\n</div>\n<form method="post" class="app-card">\n  {% csrf_token %}\n  <div class="card-header"><strong>{{ process_analysis.name }} · Version {{ process_analysis.version }}</strong><div class="small text-muted mt-1">Mit der Bestätigung werden Person, wahrgenommene Rolle und Zeitpunkt automatisch protokolliert.</div></div>\n  <div class="card-body">\n    {% if form.non_field_errors %}<div class="alert alert-danger">{{ form.non_field_errors }}</div>{% endif %}\n    {% for field in form %}<div class="mb-4"><label class="form-label" for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% if field.help_text %}<div class="form-text">{{ field.help_text }}</div>{% endif %}{% for error in field.errors %}<div class="text-danger small">{{ error }}</div>{% endfor %}</div>{% endfor %}\n    <button class="btn btn-primary" type="submit">Aktuelle Version validieren</button>\n  </div>\n</form>\n{% endblock %}\n''',
    encoding="utf-8",
)

# Migration: legacy checkbox-only validations become review-required rather than trusted.
Path("ki_radar/architecture/migrations/0007_process_validation.py").write_text(
    '''import django.db.models.deletion\nimport django.utils.timezone\nfrom django.conf import settings\nfrom django.db import migrations, models\n\n\ndef invalidate_legacy_validations(apps, schema_editor):\n    ProcessAnalysis = apps.get_model("architecture", "ProcessAnalysis")\n    ProcessAnalysis.objects.filter(status="validated").update(status="review_required")\n\n\nclass Migration(migrations.Migration):\n    dependencies = [\n        migrations.swappable_dependency(settings.AUTH_USER_MODEL),\n        ("architecture", "0006_split_value_stream_scope"),\n    ]\n\n    operations = [\n        migrations.AddField(\n            model_name="processanalysis",\n            name="version",\n            field=models.PositiveIntegerField(default=1, editable=False),\n        ),\n        migrations.AlterField(\n            model_name="processanalysis",\n            name="status",\n            field=models.CharField(\n                choices=[\n                    ("draft", "Entwurf"),\n                    ("review_required", "Prüfbedürftig"),\n                    ("validated", "Ist-Prozess validiert"),\n                    ("target_defined", "Zielbild beschrieben"),\n                ],\n                default="draft",\n                max_length=20,\n            ),\n        ),\n        migrations.CreateModel(\n            name="ProcessValidation",\n            fields=[\n                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),\n                ("created_at", models.DateTimeField(auto_now_add=True)),\n                ("updated_at", models.DateTimeField(auto_now=True)),\n                ("process_version", models.PositiveIntegerField()),\n                ("validator_role", models.CharField(max_length=100)),\n                ("validated_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),\n                ("note", models.TextField(blank=True, verbose_name="Validierungsnotiz")),\n                ("evidence_url", models.URLField(blank=True, verbose_name="Nachweis")),\n                (\n                    "process_analysis",\n                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="validations", to="architecture.processanalysis"),\n                ),\n                (\n                    "validated_by",\n                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="process_validations", to=settings.AUTH_USER_MODEL),\n                ),\n            ],\n            options={"ordering": ["-validated_at"]},\n        ),\n        migrations.AddConstraint(\n            model_name="processvalidation",\n            constraint=models.UniqueConstraint(fields=("process_analysis", "process_version"), name="unique_process_validation_version"),\n        ),\n        migrations.RunPython(invalidate_legacy_validations, migrations.RunPython.noop),\n    ]\n''',
    encoding="utf-8",
)

Path("tests/test_process_validation.py").write_text(
    '''import pytest\nfrom django.urls import reverse\n\nfrom ki_radar.architecture.forms import ProcessAnalysisForm\nfrom ki_radar.architecture.models import (\n    ProcessAnalysis,\n    ProcessValidation,\n    ValueStream,\n    ValueStreamStage,\n)\n\n\ndef make_process(owner, business_unit):\n    stream = ValueStream.objects.create(\n        name="Validierbarer Wertstrom",\n        business_unit=business_unit,\n        owner=owner,\n        trigger="Start",\n        outcome="Ergebnis",\n        scope_in="Prüfung",\n        status=ValueStream.Status.ACTIVE,\n    )\n    stage = ValueStreamStage.objects.create(\n        value_stream=stream, sequence=1, name="Prüfen"\n    )\n    return ProcessAnalysis.objects.create(\n        stage=stage,\n        name="Ist-Prozess prüfen",\n        status=ProcessAnalysis.Status.DRAFT,\n        scope_start="Anfrage liegt vor",\n        scope_end="Entscheidung ist dokumentiert",\n        trigger="Neue Anfrage",\n        outcome="Nachvollziehbare Entscheidung",\n        current_flow="Anfrage lesen und manuell prüfen",\n        roles="Fachbereich prüft",\n        systems="Fachanwendung",\n        data_objects="Anfrage und Stammdaten",\n        business_rules="Vier-Augen-Prinzip bei Sonderfällen",\n        handoffs="Übergabe an Freigabe",\n        bottlenecks="Manuelle Suche",\n        exceptions="Unvollständige Anfrage",\n        baseline_metrics="20 Minuten je Anfrage",\n        analyzed_by=owner,\n    )\n\n\ndef process_form_data(process, **overrides):\n    data = {\n        "name": process.name,\n        "status": process.status,\n        "scope_start": process.scope_start,\n        "scope_end": process.scope_end,\n        "trigger": process.trigger,\n        "outcome": process.outcome,\n        "current_flow": process.current_flow,\n        "roles": process.roles,\n        "systems": process.systems,\n        "data_objects": process.data_objects,\n        "business_rules": process.business_rules,\n        "handoffs": process.handoffs,\n        "bottlenecks": process.bottlenecks,\n        "exceptions": process.exceptions,\n        "baseline_metrics": process.baseline_metrics,\n        "target_state_principles": process.target_state_principles,\n    }\n    data.update(overrides)\n    return data\n\n\n@pytest.mark.django_db\ndef test_validated_status_cannot_be_set_in_general_process_form(owner, business_unit):\n    process = make_process(owner, business_unit)\n    form = ProcessAnalysisForm(\n        data=process_form_data(process, status=ProcessAnalysis.Status.VALIDATED),\n        instance=process,\n    )\n\n    assert form.is_valid() is False\n    assert "eigenständige Validierungsaktion" in form.errors["status"][0]\n\n\n@pytest.mark.django_db\ndef test_dedicated_validation_records_person_role_version_and_optional_evidence(\n    client, owner, business_unit\n):\n    process = make_process(owner, business_unit)\n    client.force_login(owner)\n\n    response = client.post(\n        reverse("architecture:process_analysis_validate", args=[process.pk]),\n        {\n            "note": "Ist-Ablauf im Fachworkshop bestätigt.",\n            "evidence_url": "https://example.com/process-workshop",\n        },\n    )\n\n    assert response.status_code == 302\n    process.refresh_from_db()\n    validation = ProcessValidation.objects.get(process_analysis=process)\n    assert process.status == ProcessAnalysis.Status.VALIDATED\n    assert validation.process_version == 1\n    assert validation.validated_by == owner\n    assert validation.validator_role == "Business Owner"\n    assert validation.note == "Ist-Ablauf im Fachworkshop bestätigt."\n    assert validation.validated_at is not None\n\n\n@pytest.mark.django_db\ndef test_essential_change_creates_new_version_and_requires_revalidation(\n    client, owner, business_unit\n):\n    process = make_process(owner, business_unit)\n    ProcessValidation.objects.create(\n        process_analysis=process,\n        process_version=1,\n        validated_by=owner,\n        validator_role="Business Owner",\n    )\n    process.status = ProcessAnalysis.Status.VALIDATED\n    process.save(update_fields=["status", "updated_at"])\n    client.force_login(owner)\n\n    response = client.post(\n        reverse("architecture:process_analysis_update", args=[process.pk]),\n        process_form_data(process, current_flow="Geänderter Ist-Ablauf mit zusätzlicher Prüfung"),\n    )\n\n    assert response.status_code == 302\n    process.refresh_from_db()\n    assert process.version == 2\n    assert process.status == ProcessAnalysis.Status.REVIEW_REQUIRED\n    assert process.validations.count() == 1\n    assert process.validations.get().process_version == 1\n\n\n@pytest.mark.django_db\ndef test_nonessential_status_change_does_not_invalidate_process_version(\n    client, owner, business_unit\n):\n    process = make_process(owner, business_unit)\n    client.force_login(owner)\n\n    response = client.post(\n        reverse("architecture:process_analysis_update", args=[process.pk]),\n        process_form_data(process, status=ProcessAnalysis.Status.TARGET_DEFINED),\n    )\n\n    assert response.status_code == 302\n    process.refresh_from_db()\n    assert process.version == 1\n    assert process.status == ProcessAnalysis.Status.TARGET_DEFINED\n\n\n@pytest.mark.django_db\ndef test_detail_displays_current_and_historical_validation_data(\n    client, owner, business_unit\n):\n    process = make_process(owner, business_unit)\n    ProcessValidation.objects.create(\n        process_analysis=process,\n        process_version=1,\n        validated_by=owner,\n        validator_role="Business Owner",\n        note="Workshop bestätigt.",\n        evidence_url="https://example.com/evidence",\n    )\n    process.status = ProcessAnalysis.Status.VALIDATED\n    process.save(update_fields=["status", "updated_at"])\n    client.force_login(owner)\n\n    response = client.get(process.get_absolute_url())\n\n    content = response.content.decode()\n    assert response.status_code == 200\n    assert "Validierung des Ist-Prozesses" in content\n    assert "Geprüfte Version" in content\n    assert "Business Owner" in content\n    assert "Workshop bestätigt." in content\n    assert "Validierungsnachweis öffnen" in content\n''',
    encoding="utf-8",
)
