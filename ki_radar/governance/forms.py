from django import forms
from django.utils import timezone

from .models import GovernanceAssessment


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class GovernanceAssessmentForm(forms.ModelForm):
    class Meta:
        model = GovernanceAssessment
        fields = [
            "assessment_date",
            "basis_version",
            "personal_data",
            "employee_data",
            "automated_person_assessment",
            "influences_person_decisions",
            "biometric_data",
            "safety_critical",
            "regulated_product",
            "health_safety_rights_impact",
            "external_ai_or_cloud",
            "generated_external_content",
            "human_oversight_planned",
            "privacy_review_required",
            "security_review_required",
            "legal_review_required",
            "result",
            "rationale",
            "evidence_url",
            "next_assessment_date",
        ]
        widgets = {
            "assessment_date": DateInput(),
            "next_assessment_date": DateInput(),
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
