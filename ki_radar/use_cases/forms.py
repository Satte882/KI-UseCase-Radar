from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from ki_radar.accounts.models import BusinessUnit
from ki_radar.accounts.permissions import is_coordinator

from .models import BenefitMeasurement, DecisionAssessment, StrategicObjective, UseCase


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class UseCaseForm(forms.ModelForm):
    class Meta:
        model = UseCase
        fields = [
            "title",
            "summary",
            "problem_statement",
            "business_unit",
            "affected_process",
            "target_users",
            "business_owner",
            "coordinator",
            "technical_owner",
            "priority",
            "next_review_date",
            "pilot_start",
            "planned_pilot_end",
            "solution_type",
            "hosting_type",
            "provider",
            "product_name",
            "model_name",
            "source_systems",
            "data_sources",
            "interface_description",
            "intended_users",
            "intended_purpose",
            "strategic_objective",
            "strategy_contribution",
            "expected_benefit",
            "benefit_category",
            "metric_name",
            "metric_type",
            "metric_direction",
            "metric_unit",
            "metric_baseline",
            "metric_target",
            "metric_measurement_method",
            "metric_actual",
            "metric_measurement_period",
            "metric_measured_at",
            "metric_evidence_url",
            "baseline",
            "success_criterion",
            "target_value",
            "realized_result",
            "one_time_cost",
            "recurring_cost",
            "business_value",
            "technical_feasibility",
            "data_readiness",
            "risk_complexity",
            "privacy_review_completed",
            "security_review_completed",
            "legal_review_completed",
            "human_oversight",
            "support_responsibility",
        ]
        widgets = {
            "next_review_date": DateInput(),
            "pilot_start": DateInput(),
            "planned_pilot_end": DateInput(),
            "metric_measured_at": DateInput(),
            "problem_statement": forms.Textarea(attrs={"rows": 4}),
            "summary": forms.Textarea(attrs={"rows": 2}),
            "strategy_contribution": forms.Textarea(attrs={"rows": 3}),
            "expected_benefit": forms.Textarea(attrs={"rows": 3}),
            "metric_measurement_method": forms.Textarea(attrs={"rows": 2}),
            "baseline": forms.Textarea(attrs={"rows": 2}),
            "success_criterion": forms.Textarea(attrs={"rows": 2}),
            "realized_result": forms.Textarea(attrs={"rows": 2}),
            "human_oversight": forms.Textarea(attrs={"rows": 2}),
            "support_responsibility": forms.Textarea(attrs={"rows": 2}),
        }
        help_texts = {
            "strategic_objective": (
                "Welches aktive Unternehmensziel wird durch den Use Case unterstützt?"
            ),
            "strategy_contribution": (
                "Konkreter Wirkzusammenhang zwischen Use Case, Ziel und erwarteter Veränderung."
            ),
            "metric_name": "Genau eine primäre Kennzahl, an der der Pilot bewertet wird.",
            "metric_unit": "Zum Beispiel Minuten je Rechnung, Prozent, Euro oder Fälle pro Woche.",
            "metric_measurement_method": (
                "Wie und mit welcher Stichprobe wird die Kennzahl erhoben?"
            ),
            "metric_actual": (
                "Aktueller Wert. Neue Messungen sollten über 'Nutzenmessung erfassen' "
                "dokumentiert werden."
            ),
            "metric_evidence_url": "Link auf die freigegebene Auswertung oder den Messnachweis.",
        }
        labels = {
            "title": "Titel",
            "summary": "Kurzbeschreibung",
            "problem_statement": "Problemstellung",
            "business_unit": "Organisationseinheit",
            "affected_process": "Betroffener Prozess",
            "target_users": "Zielgruppe",
            "business_owner": "Business Owner",
            "coordinator": "KI-Koordinator",
            "technical_owner": "Technischer Owner",
            "priority": "Priorität",
            "next_review_date": "Nächster Entscheidungstermin",
            "pilot_start": "Pilotbeginn",
            "planned_pilot_end": "Geplantes Pilotende",
            "solution_type": "Lösungstyp",
            "hosting_type": "Hosting",
            "provider": "Anbieter",
            "product_name": "Produktname",
            "model_name": "Modellname",
            "source_systems": "Quellsysteme",
            "data_sources": "Datenquellen",
            "interface_description": "Schnittstellenbeschreibung",
            "intended_users": "Vorgesehene Nutzer",
            "intended_purpose": "Vorgesehener Zweck",
            "strategic_objective": "Strategisches Ziel",
            "strategy_contribution": "Beitrag zum strategischen Ziel",
            "expected_benefit": "Erwarteter Nutzen",
            "benefit_category": "Nutzenkategorie",
            "baseline": "Historische Baseline",
            "success_criterion": "Historisches Erfolgskriterium",
            "target_value": "Historischer Zielwert",
            "realized_result": "Historisches Ergebnis",
            "one_time_cost": "Einmalige Kosten",
            "recurring_cost": "Laufende Kosten",
            "business_value": "Business Value",
            "technical_feasibility": "Technische Machbarkeit",
            "data_readiness": "Datenreife",
            "risk_complexity": "Risiko und Komplexität",
            "privacy_review_completed": "Datenschutzprüfung abgeschlossen",
            "security_review_completed": "Security-Prüfung abgeschlossen",
            "legal_review_completed": "Rechtsprüfung abgeschlossen",
            "human_oversight": "Menschliche Aufsicht",
            "support_responsibility": "Support-Verantwortung",
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-control"
                if not isinstance(field.widget, forms.CheckboxInput)
                else "form-check-input",
            )
        for field_name in [
            "business_unit",
            "business_owner",
            "coordinator",
            "technical_owner",
            "priority",
            "solution_type",
            "hosting_type",
            "strategic_objective",
            "metric_type",
            "metric_direction",
            "business_value",
            "technical_feasibility",
            "data_readiness",
            "risk_complexity",
        ]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["class"] = "form-select"
        self.fields["business_unit"].queryset = BusinessUnit.objects.filter(is_active=True)
        objectives = StrategicObjective.objects.filter(is_active=True)
        if self.instance.pk and self.instance.strategic_objective_id:
            objectives = StrategicObjective.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.strategic_objective_id)
            )
        self.fields["strategic_objective"].queryset = objectives.order_by("title")
        user_model = get_user_model()
        active_users = user_model.objects.filter(is_active=True, is_anonymized=False).order_by(
            "last_name", "first_name", "username"
        )
        for name in ["business_owner", "coordinator", "technical_owner"]:
            self.fields[name].queryset = active_users
        self.fields["business_owner"].required = True
        if current_user and not self.instance.pk:
            self.fields["business_owner"].initial = current_user
        if current_user and not is_coordinator(current_user):
            for name in [
                "business_owner",
                "coordinator",
                "privacy_review_completed",
                "security_review_completed",
                "legal_review_completed",
            ]:
                if name in self.fields:
                    self.fields[name].disabled = True

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("pilot_start")
        end = cleaned.get("planned_pilot_end")
        if start and end and end < start:
            self.add_error(
                "planned_pilot_end",
                "Das geplante Pilotende darf nicht vor dem Pilotbeginn liegen.",
            )

        metric_type = cleaned.get("metric_type")
        baseline = cleaned.get("metric_baseline")
        target = cleaned.get("metric_target")
        actual = cleaned.get("metric_actual")
        direction = cleaned.get("metric_direction")
        if metric_type == UseCase.MetricType.PERCENT:
            for field_name, value in [
                ("metric_baseline", baseline),
                ("metric_target", target),
                ("metric_actual", actual),
            ]:
                if value is not None and not 0 <= value <= 100:
                    self.add_error(field_name, "Prozentwerte müssen zwischen 0 und 100 liegen.")
        if baseline is not None and target is not None:
            if baseline == target:
                self.add_error(
                    "metric_target",
                    "Der Zielwert muss sich von der Baseline unterscheiden.",
                )
            elif direction == UseCase.MetricDirection.LOWER and target > baseline:
                self.add_error(
                    "metric_target",
                    "Bei 'Niedriger ist besser' muss der Zielwert unter der Baseline liegen.",
                )
            elif direction == UseCase.MetricDirection.HIGHER and target < baseline:
                self.add_error(
                    "metric_target",
                    "Bei 'Höher ist besser' muss der Zielwert über der Baseline liegen.",
                )
        if cleaned.get("strategic_objective") and not cleaned.get("strategy_contribution"):
            self.add_error(
                "strategy_contribution",
                "Der konkrete Beitrag zum gewählten strategischen Ziel muss beschrieben werden.",
            )
        return cleaned


class StrategicObjectiveForm(forms.ModelForm):
    class Meta:
        model = StrategicObjective
        fields = [
            "title",
            "description",
            "owner",
            "active_from",
            "active_until",
            "target_kpi",
            "target_value",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "active_from": DateInput(),
            "active_until": DateInput(),
        }
        labels = {
            "title": "Strategisches Ziel",
            "description": "Beschreibung",
            "owner": "Verantwortliche Person",
            "active_from": "Gültig ab",
            "active_until": "Gültig bis",
            "target_kpi": "Ziel-KPI",
            "target_value": "Zielwert",
            "is_active": "Aktiv",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-control"
                if not isinstance(field.widget, forms.CheckboxInput)
                else "form-check-input",
            )
        self.fields["owner"].widget.attrs["class"] = "form-select"
        self.fields["owner"].queryset = (
            get_user_model()
            .objects.filter(is_active=True, is_anonymized=False)
            .order_by("last_name", "first_name", "username")
        )

    def clean(self):
        cleaned = super().clean()
        active_from = cleaned.get("active_from")
        active_until = cleaned.get("active_until")
        if active_from and active_until and active_until < active_from:
            self.add_error("active_until", "Das Enddatum darf nicht vor dem Startdatum liegen.")
        return cleaned


class DecisionAssessmentForm(forms.ModelForm):
    criterion_names = [
        "business_value",
        "strategic_fit",
        "technical_feasibility",
        "data_readiness",
        "risk_complexity",
    ]

    class Meta:
        model = DecisionAssessment
        fields = [
            "assessment_date",
            "business_value",
            "business_value_confidence",
            "business_value_rationale",
            "business_value_evidence_url",
            "strategic_fit",
            "strategic_fit_confidence",
            "strategic_fit_rationale",
            "strategic_fit_evidence_url",
            "technical_feasibility",
            "technical_feasibility_confidence",
            "technical_feasibility_rationale",
            "technical_feasibility_evidence_url",
            "data_readiness",
            "data_readiness_confidence",
            "data_readiness_rationale",
            "data_readiness_evidence_url",
            "risk_complexity",
            "risk_complexity_confidence",
            "risk_complexity_rationale",
            "risk_complexity_evidence_url",
            "overall_rationale",
        ]
        widgets = {
            "assessment_date": DateInput(),
            "business_value_rationale": forms.Textarea(attrs={"rows": 3}),
            "strategic_fit_rationale": forms.Textarea(attrs={"rows": 3}),
            "technical_feasibility_rationale": forms.Textarea(attrs={"rows": 3}),
            "data_readiness_rationale": forms.Textarea(attrs={"rows": 3}),
            "risk_complexity_rationale": forms.Textarea(attrs={"rows": 3}),
            "overall_rationale": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "assessment_date": "Bewertungsdatum",
            "business_value": "Ausprägung",
            "business_value_confidence": "Evidenzsicherheit",
            "business_value_rationale": "Begründung",
            "business_value_evidence_url": "Nachweis",
            "strategic_fit": "Ausprägung",
            "strategic_fit_confidence": "Evidenzsicherheit",
            "strategic_fit_rationale": "Begründung",
            "strategic_fit_evidence_url": "Nachweis",
            "technical_feasibility": "Ausprägung",
            "technical_feasibility_confidence": "Evidenzsicherheit",
            "technical_feasibility_rationale": "Begründung",
            "technical_feasibility_evidence_url": "Nachweis",
            "data_readiness": "Ausprägung",
            "data_readiness_confidence": "Evidenzsicherheit",
            "data_readiness_rationale": "Begründung",
            "data_readiness_evidence_url": "Nachweis",
            "risk_complexity": "Ausprägung",
            "risk_complexity_confidence": "Evidenzsicherheit",
            "risk_complexity_rationale": "Begründung",
            "risk_complexity_evidence_url": "Nachweis",
            "overall_rationale": "Gesamtbegründung und offene Annahmen",
        }

    def __init__(self, *args, use_case=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_case = use_case
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        for name in self.criterion_names:
            self.fields[name].widget.attrs["class"] = "form-select"
            self.fields[f"{name}_confidence"].widget.attrs["class"] = "form-select"
        if not self.is_bound:
            from django.utils import timezone

            self.fields["assessment_date"].initial = timezone.localdate()
            if use_case:
                self.fields["business_value"].initial = use_case.business_value
                self.fields["technical_feasibility"].initial = use_case.technical_feasibility
                self.fields["data_readiness"].initial = use_case.data_readiness
                self.fields["risk_complexity"].initial = use_case.risk_complexity
                self.fields["strategic_fit"].initial = UseCase.Level.MEDIUM
            for name in self.criterion_names:
                self.fields[f"{name}_confidence"].initial = DecisionAssessment.Confidence.MEDIUM


class BenefitMeasurementForm(forms.ModelForm):
    class Meta:
        model = BenefitMeasurement
        fields = [
            "measured_at",
            "period",
            "actual_value",
            "method",
            "evidence_url",
            "variance_reason",
            "decision_consequence",
        ]
        widgets = {
            "measured_at": DateInput(),
            "method": forms.Textarea(attrs={"rows": 3}),
            "variance_reason": forms.Textarea(attrs={"rows": 3}),
            "decision_consequence": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "measured_at": "Messdatum",
            "period": "Messzeitraum",
            "actual_value": "Gemessener Ist-Wert",
            "method": "Messmethode",
            "evidence_url": "Messnachweis",
            "variance_reason": "Ursache der Zielabweichung",
            "decision_consequence": "Konsequenz für die nächste Entscheidung",
        }

    def __init__(self, *args, use_case=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_case = use_case
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        if not self.is_bound:
            from django.utils import timezone

            self.fields["measured_at"].initial = timezone.localdate()
            if use_case:
                self.fields["method"].initial = use_case.metric_measurement_method

    def clean_actual_value(self):
        value = self.cleaned_data["actual_value"]
        if (
            self.use_case
            and self.use_case.metric_type == UseCase.MetricType.PERCENT
            and not 0 <= value <= 100
        ):
            raise forms.ValidationError("Prozentwerte müssen zwischen 0 und 100 liegen.")
        return value
