from django import forms
from django.contrib.auth import get_user_model

from ki_radar.accounts.models import BusinessUnit
from ki_radar.accounts.permissions import is_coordinator

from .models import UseCase


class DateInput(forms.DateInput):
    input_type = "date"


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
            "expected_benefit": forms.Textarea(attrs={"rows": 3}),
            "metric_measurement_method": forms.Textarea(attrs={"rows": 2}),
            "baseline": forms.Textarea(attrs={"rows": 2}),
            "success_criterion": forms.Textarea(attrs={"rows": 2}),
            "realized_result": forms.Textarea(attrs={"rows": 2}),
            "human_oversight": forms.Textarea(attrs={"rows": 2}),
            "support_responsibility": forms.Textarea(attrs={"rows": 2}),
        }
        help_texts = {
            "metric_name": "Genau eine primäre Kennzahl, an der der Pilot bewertet wird.",
            "metric_unit": "Zum Beispiel Minuten je Rechnung, Prozent, Euro oder Fälle pro Woche.",
            "metric_measurement_method": (
                "Wie und mit welcher Stichprobe wird die Kennzahl erhoben?"
            ),
            "metric_actual": "Erst zum Pilotabschluss eintragen.",
            "metric_evidence_url": "Link auf die freigegebene Auswertung oder den Messnachweis.",
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
                "planned_pilot_end", "Das geplante Pilotende darf nicht vor dem Pilotbeginn liegen."
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
        return cleaned
