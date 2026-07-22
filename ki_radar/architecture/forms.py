from django import forms

from ki_radar.core.taxonomy import BusinessDomain, ScreeningLevel

from .focus import ValueStreamFocus, get_value_stream_focus
from .models import ProcessAnalysis, SolutionOption, ValueStream, ValueStreamStage

FORM_CONTROL = "form-control"
FORM_SELECT = "form-select"


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", FORM_SELECT)
            else:
                field.widget.attrs.setdefault("class", FORM_CONTROL)
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 3)


class ValueStreamForm(StyledModelForm):
    business_domain = forms.ChoiceField(
        choices=BusinessDomain.choices,
        label="Fachdomäne",
    )
    capability = forms.CharField(
        max_length=200,
        required=False,
        label="Business Capability",
    )
    strategic_impact = forms.ChoiceField(
        choices=[("", "Noch nicht bewertet"), *ScreeningLevel.choices],
        required=False,
        label="Strategischer Impact",
    )
    economic_potential = forms.ChoiceField(
        choices=[("", "Noch nicht bewertet"), *ScreeningLevel.choices],
        required=False,
        label="Wirtschaftliches Potenzial",
    )
    pain_intensity = forms.ChoiceField(
        choices=[("", "Noch nicht bewertet"), *ScreeningLevel.choices],
        required=False,
        label="Problem- und Schmerzintensität",
    )
    data_accessibility = forms.ChoiceField(
        choices=[("", "Noch nicht bewertet"), *ScreeningLevel.choices],
        required=False,
        label="Datenzugänglichkeit",
    )
    change_effort = forms.ChoiceField(
        choices=[("", "Noch nicht bewertet"), *ScreeningLevel.choices],
        required=False,
        label="Veränderungsaufwand",
    )
    focus_status = forms.ChoiceField(
        choices=ValueStreamFocus.Status.choices,
        label="Fokusentscheidung",
    )
    focus_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Begründung der Fokusentscheidung",
    )

    class Meta:
        model = ValueStream
        fields = [
            "name",
            "business_unit",
            "owner",
            "status",
            "description",
            "trigger",
            "outcome",
            "scope",
            "strategic_objective",
            "stakeholders",
            "constraints",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "trigger": forms.Textarea(attrs={"rows": 3}),
            "outcome": forms.Textarea(attrs={"rows": 3}),
            "scope": forms.Textarea(attrs={"rows": 3}),
            "strategic_objective": forms.Textarea(attrs={"rows": 3}),
            "stakeholders": forms.Textarea(attrs={"rows": 3}),
            "constraints": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        focus = get_value_stream_focus(self.instance) if self.instance.pk else None
        if focus is not None and not self.is_bound:
            self.initial.update(
                {
                    "business_domain": focus.business_domain,
                    "capability": focus.capability,
                    "strategic_impact": focus.strategic_impact,
                    "economic_potential": focus.economic_potential,
                    "pain_intensity": focus.pain_intensity,
                    "data_accessibility": focus.data_accessibility,
                    "change_effort": focus.change_effort,
                    "focus_status": focus.status,
                    "focus_rationale": focus.rationale,
                }
            )
        else:
            self.initial.setdefault("business_domain", BusinessDomain.OTHER)
            self.initial.setdefault("focus_status", ValueStreamFocus.Status.NOT_SCREENED)

    def clean(self):
        cleaned = super().clean()
        focus_status = cleaned.get("focus_status")
        if focus_status == ValueStreamFocus.Status.NOT_SCREENED:
            return cleaned
        required = {
            "capability": "Business Capability",
            "strategic_impact": "Strategischer Impact",
            "economic_potential": "Wirtschaftliches Potenzial",
            "pain_intensity": "Problem- und Schmerzintensität",
            "data_accessibility": "Datenzugänglichkeit",
            "change_effort": "Veränderungsaufwand",
            "focus_rationale": "Begründung der Fokusentscheidung",
        }
        for field_name, label in required.items():
            if not str(cleaned.get(field_name, "")).strip():
                self.add_error(field_name, f"{label} ist für eine Fokusentscheidung erforderlich.")
        return cleaned

    def save(self, commit=True):
        value_stream = super().save(commit=False)
        value_stream._focus_payload = {
            "business_domain": self.cleaned_data["business_domain"],
            "capability": self.cleaned_data.get("capability", ""),
            "strategic_impact": self.cleaned_data.get("strategic_impact", ""),
            "economic_potential": self.cleaned_data.get("economic_potential", ""),
            "pain_intensity": self.cleaned_data.get("pain_intensity", ""),
            "data_accessibility": self.cleaned_data.get("data_accessibility", ""),
            "change_effort": self.cleaned_data.get("change_effort", ""),
            "status": self.cleaned_data["focus_status"],
            "rationale": self.cleaned_data.get("focus_rationale", ""),
        }
        if commit:
            value_stream.save()
        return value_stream


class ValueStreamStageForm(StyledModelForm):
    class Meta:
        model = ValueStreamStage
        fields = [
            "sequence",
            "name",
            "description",
            "actors",
            "systems",
            "documents",
            "pain_points",
            "baseline_metrics",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "actors": forms.Textarea(attrs={"rows": 3}),
            "systems": forms.Textarea(attrs={"rows": 3}),
            "documents": forms.Textarea(attrs={"rows": 3}),
            "pain_points": forms.Textarea(attrs={"rows": 4}),
            "baseline_metrics": forms.Textarea(attrs={"rows": 3}),
        }


class ProcessAnalysisForm(StyledModelForm):
    class Meta:
        model = ProcessAnalysis
        fields = [
            "name",
            "status",
            "scope_start",
            "scope_end",
            "trigger",
            "outcome",
            "current_flow",
            "roles",
            "systems",
            "data_objects",
            "business_rules",
            "handoffs",
            "bottlenecks",
            "exceptions",
            "baseline_metrics",
            "target_state_principles",
        ]
        widgets = {
            "current_flow": forms.Textarea(attrs={"rows": 7}),
            "roles": forms.Textarea(attrs={"rows": 4}),
            "systems": forms.Textarea(attrs={"rows": 4}),
            "data_objects": forms.Textarea(attrs={"rows": 4}),
            "business_rules": forms.Textarea(attrs={"rows": 4}),
            "handoffs": forms.Textarea(attrs={"rows": 4}),
            "bottlenecks": forms.Textarea(attrs={"rows": 5}),
            "exceptions": forms.Textarea(attrs={"rows": 4}),
            "baseline_metrics": forms.Textarea(attrs={"rows": 4}),
            "target_state_principles": forms.Textarea(attrs={"rows": 5}),
        }


class SolutionOptionForm(StyledModelForm):
    def __init__(self, *args, process_analysis=None, **kwargs):
        super().__init__(*args, **kwargs)
        if process_analysis is not None:
            self.process_analysis = process_analysis
        elif self.instance.pk:
            self.process_analysis = self.instance.process_analysis
        else:
            self.process_analysis = None

    def clean_recommendation(self):
        recommendation = self.cleaned_data["recommendation"]
        if (
            recommendation != SolutionOption.Recommendation.PREFERRED
            or self.process_analysis is None
        ):
            return recommendation
        focus = get_value_stream_focus(self.process_analysis.stage.value_stream)
        if focus is None or not focus.is_selected:
            raise forms.ValidationError(
                "Eine Lösungsoption kann erst nach einer dokumentierten Auswahl des Value Streams "
                "bevorzugt werden."
            )
        existing = self.process_analysis.solution_options.filter(
            recommendation=SolutionOption.Recommendation.PREFERRED
        )
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError(
                "Für diese Prozessanalyse ist bereits eine bevorzugte Lösungsoption festgelegt."
            )
        return recommendation

    class Meta:
        model = SolutionOption
        fields = [
            "name",
            "option_type",
            "recommendation",
            "description",
            "expected_value",
            "feasibility",
            "data_requirements",
            "application_impact",
            "integration_impact",
            "technology_constraints",
            "risks",
            "architecture_fit",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "expected_value": forms.Textarea(attrs={"rows": 4}),
            "data_requirements": forms.Textarea(attrs={"rows": 4}),
            "application_impact": forms.Textarea(attrs={"rows": 4}),
            "integration_impact": forms.Textarea(attrs={"rows": 4}),
            "technology_constraints": forms.Textarea(attrs={"rows": 4}),
            "risks": forms.Textarea(attrs={"rows": 4}),
            "architecture_fit": forms.Textarea(attrs={"rows": 5}),
        }
