from django import forms
from django.utils import timezone

from .models import GovernanceAssessment


class GovernanceAssessmentForm(forms.ModelForm):
    class Meta:
        model = GovernanceAssessment
        exclude = ["use_case", "reviewer", "created_at", "updated_at"]
        widgets = {
            "assessment_date": forms.DateInput(attrs={"type": "date"}),
            "next_assessment_date": forms.DateInput(attrs={"type": "date"}),
            "rationale": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assessment_date"].initial = timezone.localdate()
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control",
            )
