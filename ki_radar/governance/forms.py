from django import forms
from django.utils import timezone

from .models import GovernanceAssessment, GovernanceReview


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
        labels = {
            "assessment_date": "Screening-Datum",
            "basis_version": "Prüfgrundlage / Version",
            "personal_data": "Personenbezogene Daten",
            "employee_data": "Beschäftigtendaten",
            "automated_person_assessment": "Automatisierte Personenbewertung",
            "influences_person_decisions": "Beeinflusst Entscheidungen über Personen",
            "biometric_data": "Biometrische Daten",
            "safety_critical": "Sicherheitskritischer Einsatz",
            "regulated_product": "Reguliertes Produkt",
            "health_safety_rights_impact": "Auswirkung auf Gesundheit, Sicherheit oder Rechte",
            "external_ai_or_cloud": "Externe KI oder Cloud",
            "generated_external_content": "Extern veröffentlichte generierte Inhalte",
            "human_oversight_planned": "Menschliche Aufsicht geplant",
            "privacy_review_required": "Datenschutzprüfung erforderlich",
            "security_review_required": "Security-Prüfung erforderlich",
            "legal_review_required": "Rechtsprüfung erforderlich",
            "result": "Ergebnis",
            "rationale": "Begründung",
            "evidence_url": "Nachweislink",
            "next_assessment_date": "Nächstes Screening",
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


class GovernanceReviewForm(forms.ModelForm):
    class Meta:
        model = GovernanceReview
        fields = ["reviewed_at", "result", "rationale", "evidence_url"]
        widgets = {
            "reviewed_at": DateInput(),
            "rationale": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "reviewed_at": "Prüfdatum",
            "result": "Prüfergebnis",
            "rationale": "Begründung und wesentliche Feststellungen",
            "evidence_url": "Nachweislink",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reviewed_at"].initial = timezone.localdate()
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
