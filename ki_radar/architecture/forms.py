from django import forms

from .models import ValueStream, ValueStreamStage

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
