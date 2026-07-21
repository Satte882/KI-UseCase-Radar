from django import forms

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
